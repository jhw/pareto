#!/usr/bin/env python

import datetime, boto3, json, re, yaml, zipfile

def lambda_key(config, component):
    timestamp=datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
    return "%s/%s-%s.zip" % (config["AppName"],
                             component["name"],
                             timestamp)

def push_lambdas(s3, config, lambdakeys):
    def push_lambda(s3, config, name, key):
        zfname="tmp/%s" % key.split("/")[-1]
        zf=zipfile.ZipFile(zfname, 'w', zipfile.ZIP_DEFLATED)
        """
        - check path exists
        - iterate over directory
        """
        zf.write("lambda/%s/index.py" % name,
                 arcname="index.py")
        zf.close()
        s3.upload_file(zfname,
                       config["S3StagingBucket"],
                       key,
                       ExtraArgs={'ContentType': 'application/zip'})
    for name, key in lambdakeys.items():
        push_lambda(s3, config, name, key)
            
def deploy_stack(cf, config, stagename, lambdakeys, stack):
    def stack_exists(cf, stackname):
        stacknames=[stack["StackName"]
                    for stack in cf.describe_stacks()["Stacks"]]
        return stackname in stacknames
    def hungarorise(text):
        return "".join([tok.capitalize()
                        for tok in re.split("\\_|\\-", text)
                        if tok!=''])
    def init_params(config, lambdakeys):
        params={"S3StagingBucket": config["S3StagingBucket"]}
        for name, key in lambdakeys.items():
            params["S3%sKey" % hungarorise(name)]=key
        return params        
    stackname="%s-%s" % (config["AppName"],
                         stagename)
    action="update" if stack_exists(cf, stackname) else "create"
    fn=getattr(cf, "%s_stack" % action)
    params=init_params(config, lambdakeys)
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
        lambdakeys={name: lambda_key(config, {"name": name})
                    for name in ["hello-function"]}
        push_lambdas(s3, config, lambdakeys)
        with open(stackfile, 'r') as f:
           stack=yaml.load(f.read(),
                           Loader=yaml.FullLoader)
        deploy_stack(cf, config, stagename, lambdakeys, stack)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
