#!/usr/bin/env python

import datetime, boto3, json, os, re, yaml, zipfile

from pareto.components.stack import synth_stack

Config=dict([tuple(row.split("="))
             for row in open("app.props").read().split("\n")
             if "=" in row])

CF, S3 = boto3.client("cloudformation"), boto3.client("s3")

def load_config(stackfile, stagename):
    with open(stackfile, 'r') as f:
        config=yaml.load(f.read(),
                         Loader=yaml.FullLoader)
    config["app"]=Config["AppName"]
    config["region"]=Config["AWSRegion"]
    config["stage"]=stagename
    return config

def lambda_keys(config):
    def lambda_key(name, timestamp):
        return "%s/%s-%s.zip" % (Config["AppName"],
                                 name,
                                 timestamp)
    timestamp=datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
    return {component["name"]: lambda_key(component["name"],
                                          timestamp)
            for component in config["components"]
            if component["type"]=="function"}

def push_lambdas(lambdakeys):
    def push_lambda(name, key):
        zfname="tmp/%s" % key.split("/")[-1]
        zf=zipfile.ZipFile(zfname, 'w', zipfile.ZIP_DEFLATED)
        """
        - check path exists
        - iterate over directory
        """
        zf.write("lambda/%s/index.py" % name,
                 arcname="index.py")
        zf.close()
        S3.upload_file(zfname,
                       Config["S3StagingBucket"],
                       key,
                       ExtraArgs={'ContentType': 'application/zip'})
    for name, key in lambdakeys.items():
        push_lambda(name, key)
            
def deploy_stack(stack, lambdakeys, stagename):
    def stack_exists(stackname):
        stacknames=[stack["StackName"]
                    for stack in CF.describe_stacks()["Stacks"]]
        return stackname in stacknames
    def hungarorise(text):
        return "".join([tok.capitalize()
                        for tok in re.split("\\_|\\-", text)
                        if tok!=''])
    def init_params(lambdakeys):
        params={"S3StagingBucket": Config["S3StagingBucket"]}
        for name, key in lambdakeys.items():
            params["S3%sKey" % hungarorise(name)]=key
        return params        
    stackname="%s-%s" % (Config["AppName"],
                         stagename)
    action="update" if stack_exists(stackname) else "create"
    fn=getattr(CF, "%s_stack" % action)
    params=init_params(lambdakeys)
    fn(StackName=stackname,
       TemplateBody=json.dumps(stack),
       Parameters=[{"ParameterKey": k,
                    "ParameterValue": v}
                   for k, v in params.items()],
       Capabilities=["CAPABILITY_IAM"])
    waiter=CF.get_waiter("stack_%s_complete" % action)
    waiter.wait(StackName=stackname)
    
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
        lambdakeys, stack = lambda_keys(config), synth_stack(config)
        print (stack)
        print (lambdakeys)
        push_lambdas(lambdakeys)
        deploy_stack(stack, lambdakeys, stagename)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
