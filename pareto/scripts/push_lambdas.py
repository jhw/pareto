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
    def write_zipfile(config, action, zf):
        path="%s/%s" % (config["globals"]["app"],
                        underscore(action["name"]))
        count=0
        for root, dirs, files in os.walk(path):
            for filename in files:
                if is_valid_path(filename):
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
    for action in config["components"]["actions"]:
        zfname=init_zipfile(config, action)
        # push_lambda(action, zfname)
        
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
        config["globals"]["key"]=(LambdaKey(app=appname,
                                            hexsha=commits[appname][0],
                                            timestamp=commits[appname][1]))
        print (config["globals"]["key"])
        # push_lambdas(config)
    except ClientError as error:
        logging.error(error)                      
    except WaiterError as error:
        logging.error(error)                      
    except RuntimeError as error:
        logging.error(error)                      


        
