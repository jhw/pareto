#!/usr/bin/env python

"""
- this script should probably be a Github Action in due course
"""

from pareto.scripts import *

from pareto.components.preprocessor import preprocess

from git import Repo

import unittest, zipfile

@toggle_aws_profile
def run_tests(config):
    logging.info("running tests")
    def index_test(component, klassname="IndexTest"):    
        modname="%s.test" % underscore(component["name"])
        try:
            mod=__import__(modname, fromlist=[klassname])
        except ModuleNotFoundError:
            raise RuntimeError("%s does not exist" % modname)
        klass=getattr(mod, klassname)
        if not klass:
            raise RuntimeError("%s does not exist in %s" % (klassname,
                                                            modname))
        return klass
    klasses=[index_test(component)
             for component in filter_functions(config["components"])]
    suite=unittest.TestSuite()
    for klass in klasses:
        suite.addTest(unittest.makeSuite(klass))
    runner=unittest.TextTestRunner()
    results=runner.run(suite)
    nfailures, nerrors = len(results.failures), len(results.errors)
    if (nfailures > 0 or nerrors > 0):
        raise RuntimeError("Tests failed with %i failures / %i errors" % (nfailures, nerrors))        
    return results

def format_commits(fn):
    def wrapped(*args, **kwargs):
        commits=fn(*args, **kwargs)
        return {k.split("/")[1].replace("_", "-"):v[0]
                for k, v in commits.items()}
    return wrapped

@format_commits
def latest_commits(repo=Repo("."),
                   roots=["lambda/%s" % path
                          for path in os.listdir("lambda")],              
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
    latest=Latest(roots=roots,
                  ignore=ignore)
    for c0, c1 in zip(commits[:-1], commits[1:]):
        diffs=diff_commits(c1, c0)
        latest.update(c1, diffs)
        if latest.complete:
            break
    if not latest.complete:
        raise RuntimeError("latest commit map is incomplete")
    return latest

def add_staging(config, commits):
    logging.info("adding staging")
    def lambda_key(name, commits, timestamp):
        return "%s/lambdas/%s-%s-%s.zip" % (config["globals"]["app"],
                                            name,
                                            timestamp,
                                            commits[name])
    ts=timestamp()
    for component in filter_functions(config["components"]):
        key=lambda_key(component["name"], commits, ts)
        component["staging"]={"bucket": config["globals"]["bucket"],
                              "key": key}

def push_lambdas(config):
    logging.info("pushing lambdas")
    def validate_lambda(component):
        if not os.path.exists("lambda/%s" % underscore(component["name"])):
            raise RuntimeError("%s lambda does not exist" % component["name"])
    def is_valid(filename, ignore=["test.py$",
                                   ".pyc$"]):
        for pat in ignore:
            if re.search(pat, filename)!=None:
                return False
        return True
    def write_zipfile(component, zf):
        path, count = "lambda/%s" % underscore(component["name"]), 0
        for root, dirs, files in os.walk(path):
            for filename in files:
                if is_valid(filename):
                    zf.write(os.path.join(root, filename),
                             arcname=filename)
                    count+=1
        if not count:
            raise RuntimeError("no files found in %s" % path)
    def init_zipfile(component):
        zfname="tmp/%s" % component["staging"]["key"].split("/")[-1]
        zf=zipfile.ZipFile(zfname, 'w', zipfile.ZIP_DEFLATED)
        write_zipfile(component, zf)
        zf.close()
        return zfname
    def push_lambda(component, zfname):
        logging.info("pushing %s" % component["staging"]["key"])
        S3.upload_file(zfname,
                       component["staging"]["bucket"],
                       component["staging"]["key"],
                       ExtraArgs={'ContentType': 'application/zip'})
    for component in filter_functions(config["components"]):
        validate_lambda(component)
        zfname=init_zipfile(component)
        push_lambda(component, zfname)
        
if __name__=="__main__":
    try:        
        init_stdout_logger(logging.INFO)
        config=load_config(sys.argv)
        preprocess(config)
        run_tests(config)
        add_staging(config, latest_commits())
        push_lambdas(config)
    except ClientError as error:
        logging.error(error)                      
    except WaiterError as error:
        logging.error(error)                      
    except RuntimeError as error:
        logging.error(error)                      


        
