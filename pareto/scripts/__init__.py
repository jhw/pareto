import datetime, boto3, json, logging, os, re, sys, time, yaml

import pandas as pd

from botocore.exceptions import ClientError, ValidationError, WaiterError

from pareto.scripts.helpers.argsparse import argsparse

from jinja2 import Template

S3=boto3.client("s3")
CF=boto3.client("cloudformation")
Logs=boto3.client("logs")
IAM=boto3.client("iam")

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
    
def filter_functions(components):
    return [component
            for component in components
            if component["type"]=="function"]

if __name__=="__main__":
    pass
