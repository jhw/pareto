#!/usr/bin/env python

import datetime, boto3, json, yaml, zipfile

def lambda_key():
    timestamp=datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
    return "lambda-%s.zip" % timestamp

def push_lambda(s3, config, lambdakey):
    zfname="tmp/%s" % lambdakey
    zf=zipfile.ZipFile(zfname, 'w', zipfile.ZIP_DEFLATED)
    zf.write("index.py", 
             arcname="index.py")
    zf.close() # important!
    s3key="%s/%s" % (config["AppName"],
                     lambdakey)
    s3.upload_file(zfname,
                   config["S3StagingBucket"],
                   s3key,
                   ExtraArgs={'ContentType': 'application/zip'})
    
def deploy_stack(cf, config, stagename, lambdakey, stack):
    def stack_exists(cf, stackname):
        stacknames=[stack["StackName"]
                    for stack in cf.describe_stacks()["Stacks"]]
        return stackname in stacknames
    stackname="%s-%s" % (config["AppName"],
                         stagename)
    params={"S3StagingBucket": config["S3StagingBucket"],
            "S3HelloFunctionKey": "%s/%s" % (config["AppName"],
                                             lambdakey)}
    action="update" if stack_exists(cf, stackname) else "create"
    fn=getattr(cf, "%s_stack" % action)
    fn(StackName=stackname,
       TemplateBody=json.dumps(stack),
       Parameters=[{"ParameterKey": k,
                    "ParameterValue": v}
                   for k, v in params.items()],
       Capabilities=["CAPABILITY_IAM"])
    waiter=cf.get_waiter("stack_%s_complete" % action)
    waiter.wait(StackName=stackname)
    
if __name__=="__main__":
    try:
        import sys, os
        if len(sys.argv) < 2:
            raise RuntimeError("Please enter stage name")
        stagename=sys.argv[1]
        if stagename not in ["dev", "prod"]:
            raise RuntimeError("Stage name is invalid")
        stackfile="tmp/template-%s.yaml" % stagename
        if not os.path.exists(stackfile):
            raise RuntimeError("Stack file does not exist")
        s3, cf = (boto3.client("s3"),
                  boto3.client("cloudformation"))
        config=dict([tuple(row.split("="))
                     for row in open("app.props").read().split("\n")
                     if "=" in row])
        lambdakey=lambda_key()
        push_lambda(s3, config, lambdakey)
        with open(stackfile, 'r') as f:
           stack=yaml.load(f.read(),
                           Loader=yaml.FullLoader)
        deploy_stack(cf, config, stagename, lambdakey, stack)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
