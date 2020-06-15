#!/usr/bin/env python

import datetime, boto3, json, os, re, unittest, yaml, zipfile

from pareto.components.stack import synth_stack

Config=dict([tuple(row.split("="))
             for row in open("app.props").read().split("\n")
             if "=" in row])

CF, S3 = boto3.client("cloudformation"), boto3.client("s3")

def list_profiles():
    config=open("%s/.aws/config" % os.path.expanduser("~")).read()
    return [re.sub("profile ", "", row[1:-1])
            for row in config.split("\n")
            if (len(row) > 2 and
                row[0]=="[" and
                row[-1]=="]")]

Profiles=list_profiles()

"""
- temporarily disable AWS creds whilst running tests to avoid messing with production environment :-/
- must have an AWS profile entitled `dummy` for this to work
"""

def toggle_aws_profile(fn):
    def wrapped(config, dummy="dummy"):
        profile=os.environ["AWS_PROFILE"]
        if dummy not in Profiles:
            raise Runtime("`%s` profile not found" % dummy)
        os.environ["AWS_PROFILE"]=dummy
        resp=fn(config)
        os.environ["AWS_PROFILE"]=profile
        return resp
    return wrapped

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

@toggle_aws_profile
def run_tests(config):
    def index_test(component, klassname="IndexTest"):    
        modname="%s.test" % component["name"].replace("-", "_")
        try:
            mod=__import__(modname, fromlist=[klassname])
        except ModuleNotFoundError:
            raise RuntimeError("%s does not exist" % modname)
        klass=getattr(mod, klassname)
        if not klass:
            raise RuntimeError("%s does not exist in %s" % (klassname,
                                                            modname))
        return klass
    klasses=[index_test(component)
             for component in config["components"]
             if component["type"]=="function"]
    suite=unittest.TestSuite()
    for klass in klasses:
        suite.addTest(unittest.makeSuite(klass))
    runner=unittest.TextTestRunner()
    results=runner.run(suite)
    nfailures, nerrors = len(results.failures), len(results.errors)
    if (nfailures > 0 or nerrors > 0):
        raise RuntimeError("Tests failed with %i failures / %i errors" % (nfailures, nerrors))        
    return results

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
        if not os.path.exists("lambda/%s" % component["name"].replace("-", "_")):
            raise RuntimeError("%s lambda does not exist" % component["name"])
    def is_valid(filename, ignore=["test.py$",
                                   ".pyc$"]):
        for pat in ignore:
            if re.search(pat, filename)!=None:
                return False
        return True
    def write_zipfile(component, zf):
        path, count = "lambda/%s" % component["name"].replace("-", "_"), 0
        for root, dirs, files in os.walk(path):
            for filename in files:
                if is_valid(filename):
                    zf.write(os.path.join(root, filename),
                             arcname=filename)
                    count+=1
        if not count:
            raise RuntimeError("no files found in %s" % path)
    def init_zipfile(component):
        zfname="tmp/%s" % component["staging"]["key"].split("/")[-1]
        zf=zipfile.ZipFile(zfname, 'w', zipfile.ZIP_DEFLATED)
        write_zipfile(component, zf)
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
    stackname="%s-%s" % (Config["AppName"],
                         stagename)
    action="update" if stack_exists(stackname) else "create"
    fn=getattr(CF, "%s_stack" % action)
    fn(StackName=stackname,
       TemplateBody=json.dumps(stack),
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
        run_tests(config)
        add_staging(config)
        push_lambdas(config)
        stack=synth_stack(config)
        dump_stack(stack)
        deploy_stack(config, stack, stagename)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
