#!/usr/bin/env python

import datetime, boto3, yaml, zipfile

def lambda_key():
   timestamp=datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
   return "lambda-%s.zip" % timestamp

def push_lambda(s3, config):
   zfname="tmp/%s" % config["LambdaKey"]
   zf=zipfile.ZipFile(zfname, 'w', zipfile.ZIP_DEFLATED)
   zf.write("index.py", 
            arcname="index.py")
   s3key="%s/%s" % (config["AppName"],
                    config["LambdaKey"])
   s3.upload_file(zfname,
                  config["S3StagingBucket"],
                  s3key)

def deploy_stack(cf, config, stack):
    stackname="%s-%s" % (config["AppName"],
                         config["StageName"])
    params={"S3StagingBucket": config["S3StagingBucket"],
            "S3HelloFunctionKey": "%/%s" % (config["AppName"],
                                            config["LambdaKey"])}
    cf.create_stack(StackName=stackname,
                    TemplateBody=json.dumps(stack),
                    Parameters=[{"ParameterKey": k,
                                 "ParameterValue": v}
                                for k, v in params.items()],
                    Capabilities=["CAPABILITY_IAM"])
    waiter=cf.get_deploy_waiter("stack_create_complete")
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
        config["StageName"]=stagename # NB
        config["LambdaKey"]=lambda_key() # NB
        print (config["LambdaKey"])
        push_lambda(s3, config)
        with open(stackfile, 'r') as f:
           stack=yaml.load(f.read(),
                           Loader=yaml.FullLoader)
        # deploy_stack(cf, config, stack)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
