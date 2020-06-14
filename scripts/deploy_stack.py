#!/usr/bin/env python

import datetime, boto3, json, re, yaml, zipfile

Config=dict([tuple(row.split("="))
             for row in open("app.props").read().split("\n")
             if "=" in row])

CF, S3 = boto3.client("cloudformation"), boto3.client("s3")

def lambda_key(name):
    timestamp=datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
    return "%s/%s-%s.zip" % (Config["AppName"],
                             name,
                             timestamp)

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
            
def deploy_stack(stagename, lambdakeys, stack):
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
        import sys, os
        if len(sys.argv) < 2:
            raise RuntimeError("Please enter stage name")
        stagename=sys.argv[1]
        if stagename not in ["dev", "prod"]:
            raise RuntimeError("Stage name is invalid")
        stackfile="tmp/template-%s.yaml" % stagename
        if not os.path.exists(stackfile):
            raise RuntimeError("Stack file does not exist")
        lambdakeys={name: lambda_key(name)
                    for name in ["hello-function"]}
        push_lambdas(lambdakeys)
        with open(stackfile, 'r') as f:
           stack=yaml.load(f.read(),
                           Loader=yaml.FullLoader)
        deploy_stack(stagename, lambdakeys, stack)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
