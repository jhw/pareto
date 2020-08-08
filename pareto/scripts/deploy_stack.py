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
        action.setdefault("staging", {})
        action["staging"]["lambda"]=staging    
    commits=LambdaCommits(config=config, s3=S3)
    for action in config["components"]["actions"]:
       add_staging(action, commits)

@assert_actions
def add_layer_staging(config):
    logging.info("adding layer staging")
    def filter_staged(config, action, packages):
        staged=[]
        for layerkwargs in action["layers"]:
            package=LayerPackage.create(config, **layerkwargs)
            if not packages.exists(package):
                raise RuntimeError("%s does not exist" % package)
            staged.append(package)
        return staged
    def assert_unique_versions(action, packages):        
        names=[package["name"]
               for package in packages]
        unames=list(set(names))
        if len(names)!=len(unames):
            raise RuntimeError("%s has multiple versions of the same package" % action["name"])
    packages=LayerPackages(config=config, s3=S3)
    for action in config["components"]["actions"]:
        if "layers" not in action:
            continue
        staged=filter_staged(config, action, packages)
        assert_unique_versions(action, staged)
        action.setdefault("staging", {})
        action["staging"]["layer"]=staged
        
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
        env.dump()
        env.push(S3)
        if args["live"]:
            env.deploy(CF)
    except ClientError as error:
        logging.error(error)                      
    except WaiterError as error:
        logging.error(error)                      
    except RuntimeError as error:
        logging.error(error)                      


        
