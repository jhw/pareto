#!/usr/bin/env python

from pareto.scripts import *

from pareto.scripts.run_tests import run_tests

from pareto.staging.lambdas import LambdaKey

from pareto.staging.commits import CommitMap

from pareto.helpers.text import underscore

import zipfile

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
        for root, dirs, files in os.walk(config["globals"]["app"]):
            for filename in files:
                if is_valid_path(filename):
                    zf.write(os.path.join(root, filename))
                    count+=1
        if not count:
            raise RuntimeError("no files found in %s" % path)
    def init_zipfile(config):
        tokens=["tmp"]+config["globals"]["key"].split("/")[-2:]
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
                S3.head_object(Bucket=config["globals"]["bucket"],
                               Key=config["globals"]["key"])
                logging.warning("%s exists" % config["globals"]["key"])
            except ClientError as error:
                return fn(config, zfname)
        return wrapped
    @check_exists
    def push_lambda(config, zfname):
        logging.info("pushing %s" % config["globals"]["key"])
        S3.upload_file(zfname,
                       config["globals"]["bucket"],
                       config["globals"]["key"],
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
        appname=config["globals"]["app"]
        config["globals"]["key"]=str(LambdaKey(app=appname,
                                               hexsha=commits[appname][0],
                                               timestamp=commits[appname][1]))
        push_lambdas(config)
    except ClientError as error:
        logging.error(error)                      
    except WaiterError as error:
        logging.error(error)                      
    except RuntimeError as error:
        logging.error(error)                      


        
