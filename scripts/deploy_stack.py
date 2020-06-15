#!/usr/bin/env python

import datetime, boto3, json, os, re, yaml, zipfile

from pareto.components.stack import synth_stack

Config=dict([tuple(row.split("="))
             for row in open("app.props").read().split("\n")
             if "=" in row])

CF, S3 = boto3.client("cloudformation"), boto3.client("s3")

def timestamp():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")

def load_config(stackfile, stagename):
    with open(stackfile, 'r') as f:
        config=yaml.load(f.read(),
                         Loader=yaml.FullLoader)
    config["app"]=Config["AppName"]
    config["region"]=Config["AWSRegion"]
    config["stage"]=stagename
    return config

def add_staging(config):
    def lambda_key(name, timestamp):
        return "%s/%s-%s.zip" % (Config["AppName"],
                                 name,
                                 timestamp)
    ts=timestamp()
    for component in config["components"]:
        if not component["type"]=="function":
            continue
        bucket=Config["S3StagingBucket"]
        key=lambda_key(component["name"], ts)
        component["staging"]={"bucket": bucket,
                              "key": key}

def push_lambdas(config):
    def validate_lambda(component):
        if not os.path.exists("lambda/%s" % component["name"]):
            raise RuntimeError("%s lambda does not exist" % component["name"])
    def init_zipfile(component):
        zfname="tmp/%s" % component["staging"]["key"].split("/")[-1]
        zf=zipfile.ZipFile(zfname, 'w', zipfile.ZIP_DEFLATED)
        zf.write("lambda/%s/index.py" % component["name"],
                 arcname="index.py")
        zf.close()
        return zfname
    def push_lambda(component, zfname):
        S3.upload_file(zfname,
                       component["staging"]["bucket"],
                       component["staging"]["key"],
                       ExtraArgs={'ContentType': 'application/zip'})
    for component in config["components"]:
        if not component["type"]=="function":
            continue
        validate_lambda(component)
        zfname=init_zipfile(component)
        push_lambda(component, zfname)
            
def deploy_stack(config, stack, stagename):
    def stack_exists(stackname):
        stacknames=[stack["StackName"]
                    for stack in CF.describe_stacks()["Stacks"]]
        return stackname in stacknames
    def hungarorise(text):
        return "".join([tok.capitalize()
                        for tok in re.split("\\_|\\-", text)
                        if tok!=''])
    def init_params(config):
        params={"S3StagingBucket": Config["S3StagingBucket"]}
        for component in config["components"]:
            if not component["type"]=="function":
                continue
            key="S3%sKey" % hungarorise(component["name"])
            params[key]=component["staging"]["key"]
        return params        
    stackname="%s-%s" % (Config["AppName"],
                         stagename)
    action="update" if stack_exists(stackname) else "create"
    fn=getattr(CF, "%s_stack" % action)
    params=init_params(config)
    fn(StackName=stackname,
       TemplateBody=json.dumps(stack),
       Parameters=[{"ParameterKey": k,
                    "ParameterValue": v}
                   for k, v in params.items()],
       Capabilities=["CAPABILITY_IAM"])
    waiter=CF.get_waiter("stack_%s_complete" % action)
    waiter.wait(StackName=stackname)

def dump_stack(stack):
    filename="tmp/stack-%s.yaml" % timestamp()
    with open(filename, 'w') as f:
        f.write(yaml.safe_dump(stack,
                               default_flow_style=False))
    
if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 3:
            raise RuntimeError("Please enter stack file, stage name")
        stackfile, stagename = sys.argv[1:3]
        if stagename not in ["dev", "prod"]:
            raise RuntimeError("Stage name is invalid")
        if not stackfile.endswith(".yaml"):
            raise RuntimeError("Stack must be a yaml file")
        if not os.path.exists(stackfile):
            raise RuntimeError("Stack file does not exist")
        config=load_config(stackfile, stagename)
        add_staging(config)
        push_lambdas(config)
        stack=synth_stack(config)
        dump_stack(stack)
        deploy_stack(config, stack, stagename)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
