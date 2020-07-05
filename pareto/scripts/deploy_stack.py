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
        add_staging(config)
        env=synth_env(config)
        yaml.SafeDumper.ignore_aliases=lambda *args: True
        master, dashboard = env.pop("master"), env.pop("dashboard")
        print (yaml.safe_dump(env,
                              default_flow_style=False))
        print (yaml.safe_dump(master,
                              default_flow_style=False))
        print (yaml.safe_dump(dashboard,
                              default_flow_style=False))
    except ClientError as error:
        logging.error(error)                      
    except WaiterError as error:
        logging.error(error)                      
    except RuntimeError as error:
        logging.error(error)                      
