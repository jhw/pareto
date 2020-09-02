#!/usr/bin/env python

from pareto.scripts import *

from pareto.staging.lambdas import LambdaKey

from pareto.staging.commits import CommitMap

from pareto.helpers.text import underscore

import zipfile

def init_staging(config, commits):
    staging={attr: config["globals"][attr]
             for attr in ["app", "bucket"]}
    commit=commits[staging["app"]]
    staging["key"]=str(LambdaKey(app=staging["app"],
                                 hexsha=commit["hexsha"],
                                 timestamp=commit["timestamp"]))
    return staging
    
def push_lambdas(s3, config):
    def is_valid_path(filename, ignore=["test.py$",
                                        ".pyc$",
                                        "__pycache__"]):
        for pat in ignore:
            if re.search(pat, filename)!=None:
                return False
        return True
    def assert_lambdas(fn):
        def wrapped(config, zf):
            if not os.path.exists(config["staging"]["app"]):
                raise RuntimeError("lambdas not found")
            return fn(config, zf)
        return wrapped
    def assert_actions(fn):
        def assert_action(config, action):
            args=[config["staging"]["app"],
                  underscore(action["name"])]
            if not os.path.exists("%s/%s" % tuple(args)):
                raise RuntimeError("no code found for %s" % action["name"])
            for mod in ["index.py", "test.py"]:
                if not os.path.exists("%s/%s/%s" % tuple(args+[mod])):
                    raise RuntimeError("%s must include %s" % (action["name"],
                                                               mod))
            index=open("%s/%s/index.py" % tuple(args)).read()
            if "def handler(" not in index:
                raise RuntimeError("handler not found in %s index.py" % action["name"])
        def wrapped(config, zf):
            for action in config["components"]["actions"]:
                assert_action(config, action)
            return fn(config, zf)
        return wrapped
    @assert_lambdas
    @assert_actions
    def write_zipfile(config, zf):
        count=0
        for root, dirs, files in os.walk(config["staging"]["app"]):
            for filename in files:
                if is_valid_path(filename):
                    zf.write(os.path.join(root, filename))
                    count+=1
        if not count:
            raise RuntimeError("no files found in %s" % path)
    def init_zipfile(config):
        tokens=["tmp"]+config["staging"]["key"].split("/")[-2:]
        zfdir, zfname = "/".join(tokens[:-1]), "/".join(tokens)        
        if not os.path.exists(zfdir):
            os.makedirs(zfdir)
        zf=zipfile.ZipFile(zfname, 'w', zipfile.ZIP_DEFLATED)
        write_zipfile(config, zf)
        zf.close()
        return zfname
    def assert_new(fn):
        def wrapped(s3, staging, zfname):
            try:
                s3.head_object(Bucket=staging["bucket"],
                               Key=staging["key"])
                logging.warning("%s exists" % staging["key"])
            except ClientError as error:
                return fn(s3, staging, zfname)
        return wrapped
    @assert_new
    def push_lambda(s3, staging, zfname):
        logging.info("pushing %s" % staging["key"])
        s3.upload_file(zfname,
                       staging["bucket"],
                       staging["key"],
                       ExtraArgs={'ContentType': 'application/zip'})
    zfname=init_zipfile(config)
    push_lambda(s3, config["staging"], zfname)
        
if __name__=="__main__":
    try:        
        init_stdout_logger(logging.INFO)
        argsconfig=yaml.safe_load("""
        - name: config
          type: file
        """)
        args=argsparse(sys.argv[1:], argsconfig)
        config=args.pop("config")
        s3=boto3.client("s3")
        validate_bucket(config, s3)
        commits=CommitMap.create(roots=[config["globals"]["app"]])
        config["staging"]=init_staging(config, commits)
        push_lambdas(s3, config)
    except ClientError as error:
        logging.error(error)                      
    except WaiterError as error:
        logging.error(error)                      
    except RuntimeError as error:
        logging.error(error)                      


        
