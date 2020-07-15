#!/usr/bin/env python

from pareto.scripts import *

def list_s3(config):
    paginator=S3.get_paginator("list_objects_v2")
    pages=paginator.paginate(Bucket=config["globals"]["bucket"],
                             Prefix=config["globals"]["app"])
    for struct in pages:
        if "Contents" in struct:
            for obj in struct["Contents"]:
                print (obj["Key"])

if __name__=="__main__":
    try:
        init_stdout_logger(logging.INFO)
        argsconfig=yaml.load("""
        - name: config
          type: file
        """, Loader=yaml.FullLoader)
        args=argsparse(sys.argv[1:], argsconfig)
        list_s3(args["config"])
    except ClientError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
