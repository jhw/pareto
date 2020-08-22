#!/usr/bin/env python

from pareto.scripts import *

from pareto.staging.lambdas import LambdaKey

import os

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

class LayerKeys(dict):

    def __init__(self, config, s3):
        dict.__init__(self)
        paginator=s3.get_paginator("list_objects_v2")
        pages=paginator.paginate(Bucket=config["globals"]["bucket"],
                                 Prefix="%s/layers" % config["globals"]["app"])
        def filter_name(key):
            return key.split("/")[-1].split(".")[0]        
        for struct in pages:
            if "Contents" in struct:
                self.update({filter_name(obj["Key"]):obj["Key"]
                             for obj in struct["Contents"]})

def assert_template_root(fn):
    def wrapped(root):
        if not os.path.exists(root):
            raise RuntimeError("%s does not exist" % root)
        return fn(root)
    return wrapped

def assert_templates(fn):
    def wrapped(root):
        if []==os.listdir(root):
            raise RuntimeError("%s has no templates" % root)
        return fn(root)
    return wrapped

def push_templates(config, dirname, s3):
    def push(config, filename, s3):
        key="%s/templates/%s" % (config["globals"]["app"],
                                 filename.split("/")[-1])
        logging.info("pushing %s to %s" % (filename, key))
        s3.upload_file(filename,
                       config["globals"]["bucket"],
                       key,
                       ExtraArgs={'ContentType': 'application/json'})
    for filename in os.listdir(dirname):
        absfilename="%s/%s" % (dirname, filename)
        push(config, absfilename, s3)

@assert_template_root
@assert_templates
def latest_templates(root):
    return "%s/%s/json" % (root, sorted(os.listdir(root))[-1])

def assert_master(fn):
    def wrapped(config, dirname, *args, **kwargs):
        if Master not in os.listdir(dirname):
            raise RuntimeError("%s not found in %s" % (Master,
                                                       dirname))
        return fn(config, dirname, *args, **kwargs)
    return fn

@assert_master
def deploy_master(config, dirname, cf):
    logging.info("deploying master template")
    def stack_exists(stackname):
        stacknames=[stack["StackName"]
                    for stack in cf.describe_stacks()["Stacks"]]
        return stackname in stacknames
    stackname="%s-%s" % (config["globals"]["app"],
                         config["globals"]["stage"])
    action="update" if stack_exists(stackname) else "create"
    body=open("%s/%s" % (dirname, Master)).read()
    fn=getattr(cf, "%s_stack" % action)
    fn(StackName=stackname,
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
        dirname=latest_templates(root="tmp/templates")
        logging.info("template source %s" % dirname)
        push_templates(config, dirname, S3)
        # deploy_master(config, dirname, CF)
    except ClientError as error:
        logging.error(error)                      
    except WaiterError as error:
        logging.error(error)                      
    except RuntimeError as error:
        logging.error(error)                      


        
