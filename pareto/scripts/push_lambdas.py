#!/usr/bin/env python

from pareto.scripts import *

from pareto.scripts.run_tests import run_tests

from pareto.staging.lambdas import *

from pareto.helpers.text import underscore

from git import Repo

import zipfile

def format_commits(fn):
    def wrapped(*args, **kwargs):
        commits=fn(*args, **kwargs)
        return {k.split("/")[1].replace("_", "-"):v
                for k, v in commits.items()}
    return wrapped

@format_commits
def latest_commits(config,
                   repo=Repo("."),
                   ignore=["test.py"]):
    logging.info("filtering latest commits")
    def diff_commits(c1, c0):
        modified=[] 
        for diff in c0.diff(c1):
            if (diff.a_blob is not None and
                diff.a_blob.path not in modified):
                modified.append(diff.a_blob.path)        
            if (diff.b_blob is not None and
                diff.b_blob.path not in modified):
                modified.append(diff.b_blob.path)        
        return modified
    class Latest(dict):
        def __init__(self, roots, ignore):
            dict.__init__(self)
            self.roots=roots
            self.ignore=ignore
        def find_root(self, diff):
            for root in self.roots:
                if diff.startswith(root):
                    return root
            return None
        def is_valid(self, diff):
            for suffix in self.ignore:
                if diff.endswith(suffix):
                    return False
            return True
        def update(self, commit, diffs):
            ts=commit.committed_datetime.strftime("%Y-%m-%d %H:%M:%S")
            for diff in diffs:
                if not self.is_valid(diff):
                    continue
                root=self.find_root(diff)
                if (root and
                    root not in self):
                    self[root]=(commit.hexsha, ts)
        @property
        def complete(self):
            return len(self)==len(self.roots)
    commits=sorted(repo.iter_commits(repo.active_branch),
                   key=lambda x: x.committed_datetime)
    commits.reverse()
    roots=["%s/%s" % (config["globals"]["src"], path)
           for path in os.listdir(config["globals"]["src"])]
    latest=Latest(roots=roots,
                  ignore=ignore)
    for c0, c1 in zip(commits[:-1], commits[1:]):
        diffs=diff_commits(c1, c0)
        latest.update(c1, diffs)
        if latest.complete:
            break
    if not latest.complete:
        raise RuntimeError("latest commit map is incomplete (if you've moved lambdas to new directory, has changed been committed ?)")
    return latest

@assert_actions
def add_staging(config, commits):
    logging.info("adding staging")
    def lambda_key(name, commits):
        return str(LambdaCommit(app=config["globals"]["app"],
                                name=name,
                                hexsha=commits[name][0],
                                timestamp=commits[name][1]))
    for action in filter_actions(config["components"]):
        key=lambda_key(action["name"], commits)
        action["staging"]={"bucket": config["globals"]["bucket"],
                              "key": key}

@assert_actions
def push_lambdas(config):
    logging.info("pushing lambdas")
    def validate_lambda(config, action):
        path="%s/%s" % (config["globals"]["src"],
                        underscore(action["name"]))
        if not os.path.exists(path):
            raise RuntimeError("%s does not exist" % path)
    def is_valid(filename, ignore=["test.py$",
                                   ".pyc$"]):
        for pat in ignore:
            if re.search(pat, filename)!=None:
                return False
        return True
    def write_zipfile(config, action, zf):
        path="%s/%s" % (config["globals"]["src"],
                        underscore(action["name"]))
        count=0
        for root, dirs, files in os.walk(path):
            for filename in files:
                if is_valid(filename):
                    zf.write(os.path.join(root, filename),
                             arcname=filename)
                    count+=1
        if not count:
            raise RuntimeError("no files found in %s" % path)
    def init_zipfile(config, action):
        tokens=["tmp"]+action["staging"]["key"].split("/")[-2:]
        zfdir, zfname = "/".join(tokens[:-1]), "/".join(tokens)        
        if not os.path.exists(zfdir):
            os.makedirs(zfdir)
        zf=zipfile.ZipFile(zfname, 'w', zipfile.ZIP_DEFLATED)
        write_zipfile(config, action, zf)
        zf.close()
        return zfname
    def check_exists(fn):
        def wrapped(action, zfname):
            try:
                S3.head_object(Bucket=action["staging"]["bucket"],
                               Key=action["staging"]["key"])
                logging.warning("%s exists" % action["staging"]["key"])
            except ClientError as error:
                return fn(action, zfname)
        return wrapped
    @check_exists
    def push_lambda(action, zfname):
        logging.info("pushing %s" % action["staging"]["key"])
        S3.upload_file(zfname,
                       action["staging"]["bucket"],
                       action["staging"]["key"],
                       ExtraArgs={'ContentType': 'application/zip'})
    for action in filter_actions(config["components"]):
        validate_lambda(config, action)
        zfname=init_zipfile(config, action)
        push_lambda(action, zfname)
        
if __name__=="__main__":
    try:        
        init_stdout_logger(logging.INFO)
        argsconfig=yaml.safe_load("""
        - name: config
          type: file
        """)
        args=argsparse(sys.argv[1:], argsconfig)
        config=args.pop("config")
        validate_bucket(config)
        run_tests(config)
        commits=latest_commits(config)
        add_staging(config, commits)
        push_lambdas(config)
    except ClientError as error:
        logging.error(error)                      
    except WaiterError as error:
        logging.error(error)                      
    except RuntimeError as error:
        logging.error(error)                      


        
