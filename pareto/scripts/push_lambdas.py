#!/usr/bin/env python

from pareto.scripts import *

from pareto.scripts.run_tests import run_tests

from pareto.staging.lambdas import LambdaKey

from pareto.staging.commits import CommitMap

import zipfile

def init_staging(config, commits):
    staging={attr: config["globals"][attr]
             for attr in ["app", "bucket"]}
    staging["key"]=str(LambdaKey(app=staging["app"],
                                 hexsha=commits[staging["app"]][0],
                                 timestamp=commits[staging["app"]][1]))
    return staging
    
@assert_actions
def push_lambdas(config):
    logging.info("pushing lambdas")
    def is_valid_path(filename, ignore=["test.py$",
                                        ".pyc$"]):
        for pat in ignore:
            if re.search(pat, filename)!=None:
                return False
        return True
    def assert_lambdas(fn):
        def wrapped(staging, zf):
            if not os.path.exists(staging["app"]):
                raise RuntimeError("lambdas not found")
            return fn(staging, zf)
        return wrapped
    @assert_lambdas
    def write_zipfile(staging, zf):
        count=0
        for root, dirs, files in os.walk(staging["app"]):
            for filename in files:
                if is_valid_path(filename):
                    zf.write(os.path.join(root, filename))
                    count+=1
        if not count:
            raise RuntimeError("no files found in %s" % path)
    def init_zipfile(staging):
        tokens=["tmp"]+staging["key"].split("/")[-2:]
        zfdir, zfname = "/".join(tokens[:-1]), "/".join(tokens)        
        if not os.path.exists(zfdir):
            os.makedirs(zfdir)
        zf=zipfile.ZipFile(zfname, 'w', zipfile.ZIP_DEFLATED)
        write_zipfile(staging, zf)
        zf.close()
        return zfname
    def assert_new(fn):
        def wrapped(staging, zfname):
            try:
                S3.head_object(Bucket=staging["bucket"],
                               Key=staging["key"])
                logging.warning("%s exists" % staging["key"])
            except ClientError as error:
                return fn(staging, zfname)
        return wrapped
    @assert_new
    def push_lambda(staging, zfname):
        logging.info("pushing %s" % staging["key"])
        S3.upload_file(zfname,
                       staging["bucket"],
                       staging["key"],
                       ExtraArgs={'ContentType': 'application/zip'})
    zfname=init_zipfile(config["staging"])
    push_lambda(config["staging"], zfname)
        
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
        commits=CommitMap.create(roots=[config["globals"]["app"]])
        config["staging"]=init_staging(config, commits)
        push_lambdas(config)
    except ClientError as error:
        logging.error(error)                      
    except WaiterError as error:
        logging.error(error)                      
    except RuntimeError as error:
        logging.error(error)                      


        
