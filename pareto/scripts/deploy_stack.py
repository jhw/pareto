#!/usr/bin/env python

from pareto.scripts import *

from pareto.staging.lambdas import *
from pareto.staging.layers import *

from pareto.env import synth_env

def init_region(config):
    region=boto3.session.Session().region_name
    if region in ['', None]:
        raise RuntimeError("region is not set in AWS profile")
    config["globals"]["region"]=region

@assert_actions
def add_lambda_staging(config):
    logging.info("adding lambda staging")
    def add_staging(action, commits):
        groups, latest = commits.grouped, commits.latest
        staging={"bucket": config["globals"]["bucket"]}
        if "commit" in action: 
            if action["commit"] not in groups[action["name"]]:
                raise RuntimeError("commit %s not found for %s" % (action["commit"], action["name"]))
            staging["key"]=str(groups[action["name"]][action["commit"]])
        else:
            if action["name"] not in latest:
                raise RuntimeError("no deployables found for %s" % action["name"])
            staging["key"]=str(latest[action["name"]])
        action["staging"]=staging    
    commits=Lambdas(config=config, s3=S3)
    for action in filter_actions(config["components"]):
       add_staging(action, commits)

@assert_layers
def add_layer_staging(config):
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
        env.push(S3)
        if args["live"]:
            env.deploy(CF)
    except ClientError as error:
        logging.error(error)                      
    except WaiterError as error:
        logging.error(error)                      
    except RuntimeError as error:
        logging.error(error)                      


        
