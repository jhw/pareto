#!/usr/bin/env python

from pareto.scripts import *

from pareto.scripts.run_tests import run_tests

from pareto.staging.lambdas import LambdaKey

from pareto.staging.commits import CommitMap

from pareto.helpers.text import underscore

import zipfile

def format_commits(fn):
    def wrapped(*args, **kwargs):
        commits=fn(*args, **kwargs)
        return {k.split("/")[1].replace("_", "-"):v
                for k, v in commits.items()}
    return wrapped

@assert_actions
def add_staging(config, commits):
    logging.info("adding staging")
    def lambda_key(name, commits):
        return str(LambdaKey(app=config["globals"]["app"],
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
        commits=CommitMap.create(config)
        add_staging(config, commits)
        push_lambdas(config)
    except ClientError as error:
        logging.error(error)                      
    except WaiterError as error:
        logging.error(error)                      
    except RuntimeError as error:
        logging.error(error)                      


        
