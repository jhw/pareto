import datetime, boto3, json, logging, os, re, sys, time, unittest, yaml

from botocore.exceptions import ClientError, ValidationError, WaiterError

from argsparse import argsparse

import pandas as pd

from jinja2 import Template

CF, S3, Logs = boto3.client("cloudformation"), boto3.client("s3"), boto3.client("logs")

# https://stackoverflow.com/questions/14058453/making-python-loggers-output-all-messages-to-stdout-in-addition-to-log-file

def init_stdout_logger(level):
    root=logging.getLogger()
    root.setLevel(level)
    handler=logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    formatter=logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)    
    
def timestamp():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")

def filter_functions(components):
    return [component
            for component in components
            if component["type"]=="function"]

def underscore(text):
    return text.replace("-", "_")

def validate_bucket(config):
    bucketnames=[bucket["Name"]
                 for bucket in S3.list_buckets()["Buckets"]]
    if config["globals"]["bucket"] not in bucketnames:
        raise RuntimeError("bucket %s does not exist" % config["globals"]["bucket"])

    
"""
- timestamp before hexsha so deployables can be sorted
"""
        
class LambdaKey(dict):

    @classmethod
    def parse(self, s3key):
        key=LambdaKey()
        def pop_timestamp(tokens):
            ts=[int(tokens.pop())
                for i in range(6)]
            ts.reverse()
            return datetime.datetime(*ts)
        tokens=s3key.split("/")
        key["app"]=tokens[0]
        tokens=tokens[-1].split(".")[0].split("-")
        key["hexsha"]=tokens.pop()
        key["timestamp"]=pop_timestamp(tokens)
        key["name"]="-".join(tokens)
        return key

    def __init_(self, kwargs={}):
        dict.__init__(self, kwargs)

    def __str__(self):
        def format_timestamp(value):
            if isinstance(value, datetime.datetime):
                return value.strftime("%Y-%m-%d-%H-%M-%S")
            else:
                return re.sub("\\W", "-", str(value))
        return "%s/lambdas/%s-%s-%s.zip" % (self["app"],
                                            self["name"],
                                            format_timestamp(self["timestamp"]),
                                            self["hexsha"])
    
class LambdaKeys(list):

    def __init__(self, config):
        list.__init__(self)
        paginator=S3.get_paginator("list_objects_v2")
        pages=paginator.paginate(Bucket=config["globals"]["bucket"],
                                 Prefix="%s/lambdas" % config["globals"]["app"])
        for struct in pages:
            if "Contents" in struct:
                self+=[obj["Key"] for obj in struct["Contents"]]
                
    @property
    def latest(self):
        keys={}
        for s3key in sorted(self):
            key=LambdaKey.parse(s3key)
            keys[key["name"]]=s3key
        return keys

    @property
    def commits(self):
        keys={}
        for s3key in self:
            key=LambdaKey.parse(s3key)
            keys.setdefault(key["name"], {})
            keys[key["name"]][key["hexsha"]]=s3key
        return keys

def layer_project_name(config, package):
    return "%s-%s-layer" % (config["globals"]["app"],
                            package["name"])
    
def validate_layer_package(fn):
    def wrapped(packagestr):
        if ("-" in packagestr and
            not re.search("\\-(\\d+\\.)*\\d+$", packagestr)):
            raise RuntimeError("package definition has invalid format")
        return fn(packagestr)
    return wrapped

@validate_layer_package
def parse_layer_package(packagestr):
    tokens=packagestr.split("-")
    package={"name": tokens[0]}
    if len(tokens) > 1:
        package["version"]={"raw": tokens[1],
                            "formatted": tokens[1].replace(".", "-")}
    return package
    
class LambdaKeyTest(unittest.TestCase):

    App="my-app"
    Name="hello-world"
    Timestamp=datetime.datetime(*[1970, 12, 20, 19, 30, 0])
    Hexsha="ABCDEFGH"

    Key="my-app/lambdas/hello-world-1970-12-20-19-30-00-ABCDEFGH.zip"
    
    def test_new(self):
        key=LambdaKey(**{attr: getattr(self, attr.capitalize())
                         for attr in ["app", "name", "timestamp", "hexsha"]})
        self.assertEqual(str(key), self.Key)

    def test_parse(self):
        key=LambdaKey.parse(self.Key)
        for attr in ["app", "name", "timestamp", "hexsha"]:
            self.assertEqual(key[attr], getattr(self, attr.capitalize()))
            
if __name__=="__main__":
    unittest.main()
