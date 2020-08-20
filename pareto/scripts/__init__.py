import datetime, boto3, json, logging, os, re, requests, sys, time, unittest, yaml

from botocore.exceptions import ClientError, WaiterError

from pareto.scripts.helpers.outputs import Outputs

from pareto.scripts.helpers.argsparse import argsparse

"""
- warnings because pandas is noisy
"""

import warnings

warnings.simplefilter("ignore", UserWarning)

import pandas as pd

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

"""
- actions are mandatory
"""
    
def assert_actions(fn):
    def wrapped(*args, **kwargs):
        config=kwargs["config"] if "config" in kwargs else args[0]
        if "actions" in config["components"]:
            return fn(*args, **kwargs)
    return wrapped

def assert_layers(fn):
    def wrapped(*args, **kwargs):
        config=kwargs["config"] if "config" in kwargs else args[0]
        if "layers" in config["components"]:
            return fn(*args, **kwargs)
    return wrapped

def filter_actions(components):
    actions=[]
    for attr in ["actions"]:
        if attr in components:
            actions+=components[attr]
    return actions

if __name__=="__main__":
    pass
