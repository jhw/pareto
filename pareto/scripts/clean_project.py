#!/usr/bin/env python

from pareto.scripts import *

def clean_s3(config):
    paginator=S3.get_paginator("list_objects_v2")
    pages=paginator.paginate(Bucket=config["globals"]["bucket"],
                             Prefix=config["globals"]["app"])
    for struct in pages:
        if "Contents" in struct:
            for obj in struct["Contents"]:                    
                print ("deleting file %s" % obj["Key"])
                S3.delete_object(Bucket=config["globals"]["bucket"],
                                 Key=obj["Key"])                    

def clean_iam(config):
    pass

def clean_codebuild(config):
    for projectname in CB.list_projects()["projects"]:
        if not projectname.startswith(config["globals"]["app"]):
            continie
        print ("deleting project %s" % projectname)
        CB.delete_project(name=projectname)
                
if __name__=="__main__":
    try:
        init_stdout_logger(logging.INFO)
        argsconfig=yaml.load("""
        - name: config
          type: file
        """, Loader=yaml.FullLoader)
        args=argsparse(sys.argv[1:], argsconfig)
        # clean_s3(args["config"])
        # clean_iam(args["config"])
        clean_codebuild(args["config"])
    except ClientError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
