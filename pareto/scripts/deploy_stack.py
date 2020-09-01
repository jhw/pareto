#!/usr/bin/env python

from pareto.scripts import *

from pareto.helpers.text import hungarorise

from pareto.staging.lambdas import LambdaKey

import os, zipfile

Master="master.json"

class LambdaKeys(list):

    def __init__(self, config, s3):
        list.__init__(self)
        paginator=s3.get_paginator("list_objects_v2")
        pages=paginator.paginate(Bucket=config["globals"]["bucket"],
                                 Prefix="%s/lambdas" % config["globals"]["app"])
        for struct in pages:
            if "Contents" in struct:
                self+=[LambdaKey.create_s3(obj["Key"])
                       for obj in struct["Contents"]]

    def validate(self):
        return len(self) > 0
                
    @property
    def latest(self):
        return sorted(self, key=lambda x: x["timestamp"])[-1]
        
class LayerKeys(dict):

    def __init__(self, config, s3):
        dict.__init__(self)
        self.config=config
        paginator=s3.get_paginator("list_objects_v2")
        pages=paginator.paginate(Bucket=config["globals"]["bucket"],
                                 Prefix="%s/layers" % config["globals"]["app"])
        def filter_name(key):
            return key.split("/")[-1].split(".")[0]        
        for struct in pages:
            if "Contents" in struct:
                self.update({filter_name(obj["Key"]):obj["Key"]
                             for obj in struct["Contents"]})

    def validate(self):
        if "layers" in self.config["components"]:
            for layer in self.config["components"]["layers"]:
                if layer["name"] not in self:
                    raise RuntimeError("no %s layer found" % layer["name"])

def init_staging(config, s3=S3):
    lambdas, layers = LambdaKeys(config, s3), LayerKeys(config, s3)
    lambdas.validate()
    layers.validate()
    return {"lambdas": str(lambdas.latest), # NB str()
            "layers": layers}
                
def assert_zipfile_root(fn):
    def wrapped(root):
        if not os.path.exists(root):
            raise RuntimeError("%s does not exist" % root)
        return fn(root)
    return wrapped

def assert_zipfiles(fn):
    def wrapped(root):
        if []==os.listdir(root):
            raise RuntimeError("%s has no templates" % root)
        return fn(root)
    return wrapped

@assert_zipfile_root
@assert_zipfiles
def latest_zipfile(root):
    return "%s/%s" % (root, sorted(os.listdir(root))[-1])

def push_templates(config, zf, s3):
    def push(config, zf, item, s3):
        key="%s/templates/%s" % (config["globals"]["app"],
                                 item.filename)
        body=zf.open(item.filename).read()
        logging.info("pushing %s to %s" % (item.filename, key))
        s3.put_object(Bucket=config["globals"]["bucket"],
                      Key=key,
                      Body=body,
                      ContentType="application/json")
    for item in zf.infolist():
        if not item.filename.endswith(".json"):
            continue
        push(config, zf, item, s3)

def assert_master(fn):
    def wrapped(config, zf, *args, **kwargs):
        try:
            zf.getinfo(Master)
            return fn(config, zf, *args, **kwargs)
        except KeyError as error:
            raise RuntimeError("%s not found in zipfile" % Master)
    return fn

@assert_master
def deploy_master(config, staging, zf, cf):
    logging.info("deploying master template")
    def stack_exists(stackname):
        stacknames=[stack["StackName"]
                    for stack in cf.describe_stacks()["Stacks"]]
        return stackname in stacknames
    def init_params(config, staging):
        params={"AppName": config["globals"]["app"],
                "StageName": config["globals"]["stage"],
                "StagingBucket": config["globals"]["bucket"],
                "RuntimeVersion": config["globals"]["runtime"],
                "LambdaStagingKey": staging["lambdas"]}
        for k, v in staging["layers"].items():
            params["%sLayerStagingKey" % hungarorise(k)]=v
        return params
    def format_params(params):
        return [{"ParameterKey": k,
                 "ParameterValue": v}
                for k, v in params.items()]
    stackname="%s-%s" % (config["globals"]["app"],
                         config["globals"]["stage"])
    action="update" if stack_exists(stackname) else "create"
    params=init_params(config, staging)
    body=zf.open(Master).read().decode("utf8")
    fn=getattr(cf, "%s_stack" % action)
    fn(StackName=stackname,
       Parameters=format_params(params),
       TemplateBody=body,
       Capabilities=["CAPABILITY_IAM"])
    waiter=cf.get_waiter("stack_%s_complete" % action)
    waiter.wait(StackName=stackname)

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
        """)
        args=argsparse(sys.argv[1:], argsconfig)
        config=args.pop("config")
        config["globals"]["stage"]=args.pop("stage")
        staging=init_staging(config)
        zfname=latest_zipfile(root="tmp/templates")
        logging.info("template source %s" % zfname)
        zf=zipfile.ZipFile(zfname)
        push_templates(config, zf, S3)
        deploy_master(config, staging, zf, CF)
    except ClientError as error:
        logging.error(error)                      
    except WaiterError as error:
        logging.error(error)                      
    except RuntimeError as error:
        logging.error(error)                      


        
