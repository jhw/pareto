#!/usr/bin/env python

from pareto.scripts import *

from pareto.staging.layers import Layers

from pareto.env import synth_env

def init_region(config):
    region=boto3.session.Session().region_name
    if region in ['', None]:
        raise RuntimeError("region is not set in AWS profile")
    config["globals"]["region"]=region

def init_staging(config):
    return {}
    
@assert_actions
def add_lambda_staging(config):
    for action in config["components"]["actions"]:
        action["staging"]=init_staging(config)
       
@assert_layers
def add_layer_staging(config):
    for layer in config["components"]["layers"]:
        layer["staging"]=init_staging(config)

if __name__=="__main__":
    try:        
        init_stdout_logger(logging.INFO)
        argsconfig=yaml.safe_load("""
        - name: config
          type: file
        """)
        args=argsparse(sys.argv[1:], argsconfig)
        config=args.pop("config")
        init_region(config)    
        validate_bucket(config)
        add_lambda_staging(config)
        add_layer_staging(config)
        synth_env(config)
    except ClientError as error:
        logging.error(error)                      
    except WaiterError as error:
        logging.error(error)                      
    except RuntimeError as error:
        logging.error(error)                      


        
