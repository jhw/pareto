import datetime, boto3, json, logging, os, re, sys, time, unittest, yaml

import pandas as pd

from botocore.exceptions import ClientError, ValidationError, WaiterError

from pareto.scripts.helpers.argsparse import argsparse

S3=boto3.client("s3")
CF=boto3.client("cloudformation")
Logs=boto3.client("logs")
IAM=boto3.client("iam")
CB=boto3.client("codebuild")
CG=boto3.client("cognito-idp")

# https://stackoverflow.com/questions/14058453/making-python-loggers-output-all-messages-to-stdout-in-addition-to-log-file

def init_stdout_logger(level):
    root=logging.getLogger()
    root.setLevel(level)
    handler=logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    formatter=logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)    

def validate_bucket(config):
    bucketnames=[bucket["Name"]
                 for bucket in S3.list_buckets()["Buckets"]]
    if config["globals"]["bucket"] not in bucketnames:
        raise RuntimeError("bucket %s does not exist" % config["globals"]["bucket"])

def assert_actions(fn):
    def wrapped(*args, **kwargs):
        config=kwargs["config"] if "config" in kwargs else args[0]
        if "actions" not in config["components"]:
            raise RuntimeError("No actions found")
        return fn(*args, **kwargs)
    return wrapped

"""
- because services are also actions
- for now, keep referring to all lambdas as actions since lambda is a protected keyword
"""

def filter_actions(components):
    actions=[]
    for attr in ["actions", "services"]:
        if attr in components:
            actions+=components[attr]
    return actions

if __name__=="__main__":
    pass
