#!/usr/bin/env python

import datetime, boto3, yaml, zipfile

def push_lambda(s3, config):
    timestamp=datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
    zfname="tmp/lambda-%s.zip" % timestamp
    zf=zipfile.ZipFile(zfname, 'w', zipfile.ZIP_DEFLATED)
    zf.write("index.py", 
             arcname="index.py")
    s3key="%s/%s" % (config["AppName"],
                     zfname.split("/")[-1])
    s3.upload_file(zfname,
                   config["S3StagingBucket"],
                   s3key)

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
        with open(stackfile, 'r') as f:
            stack=yaml.load(f.read(),
                            Loader=yaml.FullLoader)            
        s3=boto3.client("s3")
        config=dict([tuple(row.split("="))
                     for row in open("app.props").read().split("\n")
                     if "=" in row])
        push_lambda(s3, config)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
