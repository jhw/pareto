#!/usr/bin/env python

from pareto.scripts import *

from pareto.staging.lambdas import *

from pareto.staging.layers import *

from pareto.staging.commits import CommitMap

from pareto.env import synth_env

def init_region(config):
    region=boto3.session.Session().region_name
    if region in ['', None]:
        raise RuntimeError("region is not set in AWS profile")
    config["globals"]["region"]=region

@assert_actions
def add_lambda_staging(config):
    logging.info("adding lambda staging")
    def filter_latest(config):
        keys=LambdaKeys(config=config, s3=S3)
        if keys==[]:
            raise RuntimeError("no lambdas found")
        return sorted([str(key)
                       for key in keys])[-1]
    staging={attr: config["globals"][attr]
             for attr in ["app", "bucket"]}
    staging["key"]=filter_latest(config)
    for action in config["components"]["actions"]:
        action["staging"]=staging
       
@assert_layers
def add_layer_staging(config):
    logging.info("adding layer staging")
    layers=Layers(config=config, s3=S3)
    for layer in config["components"]["layers"]:
        if layer["name"] not in layers:
            raise RuntimeError("layer %s does not exist" % layer["name"])
        layer["staging"]=layers[layer["name"]]

if __name__=="__main__":
    try:        
        init_stdout_logger(logging.INFO)
        argsconfig=yaml.safe_load("""
        - name: config
          type: file
        - name: stage
          type: enum
          options:
          - dev
          - prod
        - name: live
          type: bool
        """)
        args=argsparse(sys.argv[1:], argsconfig)
        config=args.pop("config")
        config["globals"]["stage"]=args.pop("stage")
        init_region(config)    
        validate_bucket(config)
        add_lambda_staging(config)
        add_layer_staging(config)
        env=synth_env(config)
        if args["live"]:
            env.push(S3)
            env.deploy(CF)
    except ClientError as error:
        logging.error(error)                      
    except WaiterError as error:
        logging.error(error)                      
    except RuntimeError as error:
        logging.error(error)                      


        
