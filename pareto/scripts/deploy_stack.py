#!/usr/bin/env python

from pareto.scripts import *

import unittest, zipfile

from pareto.components.preprocessor import preprocess

from pareto.components.env import synth_env

def load_config(configfile, stagename):
    with open(configfile, 'r') as f:
        config=yaml.load(f.read(),
                         Loader=yaml.FullLoader)
    config["app"]=Config["AppName"]
    config["region"]=Config["AWSRegion"]
    config["bucket"]=Config["S3StagingBucket"]
    config["stage"]=stagename
    return config

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

def add_staging(config):
    def lambda_key(name, timestamp):
        return "%s/%s-%s.zip" % (Config["AppName"],
                                 name,
                                 timestamp)
    ts=timestamp()
    for component in filter_functions(config["components"]):
        bucket=Config["S3StagingBucket"]
        key=lambda_key(component["name"], ts)
        component["staging"]={"bucket": bucket,
                              "key": key}
        
if __name__=="__main__":
    try:
        init_stdout_logger(logging.INFO)
        if len(sys.argv) < 3:
            raise RuntimeError("Please enter config file, stage name")
        configfile, stagename = sys.argv[1:3]
        if not configfile.endswith(".yaml"):
            raise RuntimeError("Config must be a yaml file")
        if not os.path.exists(configfile):
            raise RuntimeError("Config file does not exist")
        if stagename not in ["dev", "prod"]:
            raise RuntimeError("Stage name is invalid")
        config=load_config(configfile, stagename)
        preprocess(config)
        run_tests(config)
        add_staging(config)
        env=synth_env(config)
        # print (env)
    except ClientError as error:
        logging.error(error)                      
    except WaiterError as error:
        logging.error(error)                      
    except RuntimeError as error:
        logging.error(error)                      


        
