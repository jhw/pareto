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
    def check_exists(fn):
        def wrapped(config, zfname):
            try:
                S3.head_object(Bucket=config["staging"]["bucket"],
                               Key=config["staging"]["key"])
                logging.warning("%s exists" % config["staging"]["key"])
            except ClientError as error:
                return fn(config, zfname)
        return wrapped
    @check_exists
    def push_lambda(config, zfname):
        logging.info("pushing %s" % config["staging"]["key"])
        S3.upload_file(zfname,
                       config["staging"]["bucket"],
                       config["staging"]["key"],
                       ExtraArgs={'ContentType': 'application/zip'})
    zfname=init_zipfile(config)
    push_lambda(config, zfname)
        
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


        
