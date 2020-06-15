import datetime, boto3, json, logging, os, re, sys, yaml

from botocore.exceptions import ClientError, WaiterError

import pandas as pd

Config=dict([tuple(row.split("="))
             for row in open("app.props").read().split("\n")
             if "=" in row])

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
