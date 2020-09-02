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

# https://stackoverflow.com/questions/14058453/making-python-loggers-output-all-messages-to-stdout-in-addition-to-log-file

def init_stdout_logger(level):
    root=logging.getLogger()
    root.setLevel(level)
    handler=logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    formatter=logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)    

def validate_bucket(config, s3=boto3.client("s3")):
    bucketnames=[bucket["Name"]
                 for bucket in s3.list_buckets()["Buckets"]]
    if config["globals"]["bucket"] not in bucketnames:
        raise RuntimeError("bucket %s does not exist" % config["globals"]["bucket"])

if __name__=="__main__":
    pass
