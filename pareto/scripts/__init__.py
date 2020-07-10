import datetime, boto3, json, logging, os, re, sys, yaml

from botocore.exceptions import ClientError, ValidationError, WaiterError

import pandas as pd

CF, S3 = boto3.client("cloudformation"), boto3.client("s3")

# https://stackoverflow.com/questions/14058453/making-python-loggers-output-all-messages-to-stdout-in-addition-to-log-file

def init_stdout_logger(level):
    root=logging.getLogger()
    root.setLevel(level)
    handler=logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    formatter=logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)

def load_config(args):    
    def validate_configfile(configfile):
        if not configfile.endswith(".yaml"):
            raise RuntimeError("config must be a yaml file")
        if not os.path.exists(configfile):
            raise RuntimeError("config file does not exist")
    def validate_stagename(stagename):
        if stagename not in ["dev", "prod"]:
            raise RuntimeError("stage name is invalid")
    def load_config(configfile):
        with open(configfile, 'r') as f:
            config=yaml.load(f.read(),
                             Loader=yaml.FullLoader)
        return config
    def init_region(config):
        region=boto3.session.Session().region_name
        if region in ['', None]:
            raise RuntimeError("region is not set in AWS profile")
        config["globals"]["region"]=region
    def validate_bucket(config):
        bucketnames=[bucket["Name"]
                     for bucket in S3.list_buckets()["Buckets"]]
        if config["globals"]["bucket"] not in bucketnames:
            raise RuntimeError("bucket %s does not exist" % config["globals"]["bucket"])
    if len(args) < 3:
        raise RuntimeError("please enter config file, stage name")
    configfile, stagename = args[1:3]
    validate_configfile(configfile)
    validate_stagename(stagename)
    config=load_config(configfile)    
    config["globals"]["stage"]=stagename
    init_region(config)
    validate_bucket(config)
    return config    
    
"""
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cloudformation-limits.html
"""

def list_profiles():
    config=open("%s/.aws/config" % os.path.expanduser("~")).read()
    return [re.sub("profile ", "", row[1:-1])
            for row in config.split("\n")
            if (len(row) > 2 and
                row[0]=="[" and
                row[-1]=="]")]

Profiles=list_profiles()

"""
- temporarily disable AWS creds whilst running tests to avoid messing with production environment :-/
- must have an AWS profile entitled `dummy` for this to work
"""

def toggle_aws_profile(fn):
    def wrapped(config, dummy="dummy"):
        profile=os.environ["AWS_PROFILE"]
        if dummy not in Profiles:
            raise Runtime("`%s` profile not found" % dummy)
        logging.info("blanking AWS profile")
        os.environ["AWS_PROFILE"]=dummy
        resp=fn(config)
        logging.info("resetting AWS profile")
        os.environ["AWS_PROFILE"]=profile
        return resp
    return wrapped

def timestamp():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")

def filter_functions(components):
    return [component
            for component in components
            if component["type"]=="function"]

def underscore(text):
    return text.replace("-", "_")

if __name__=="__main__":
    pass
