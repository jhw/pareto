#!/usr/bin/env python

from pareto.scripts import *

def empty_bucket(bucketname):
    try:
        paginator=S3.get_paginator("list_objects_v2")
        pages=paginator.paginate(Bucket=bucketname)
        for struct in pages:
            if "Contents" in struct:
                for obj in struct["Contents"]:
                    logging.info("deleting object %s" % obj["Key"])
                    S3.delete_object(Bucket=bucketname,
                                     Key=obj["Key"])
    except ClientError as error:
        if error.response["Error"]["Code"] not in ["NoSuchBucket"]:
            raise error

def detach_policies(rolename):
    try:
        for policy in IAM.list_attached_role_policies(RoleName=rolename)["AttachedPolicies"]:
            logging.info("detaching policy %s" % policy["PolicyArn"])
            IAM.detach_role_policy(RoleName=rolename,
                                   PolicyArn=policy["PolicyArn"])
    except ClientError as error:
        if error.response["Error"]["Code"] not in ["NoSuchEntity"]:
            raise error
            
def delete_stack(stackname):
    logging.info("deleting stack %s" % stackname)
    resources=CF.describe_stack_resources(StackName=stackname)["StackResources"]
    for resource in resources:
        if resource["ResourceType"]=="AWS::S3::Bucket":
            empty_bucket(resource["PhysicalResourceId"])
        if resource["ResourceType"]=="AWS::IAM::Role":
            detach_policies(resource["PhysicalResourceId"])
    CF.delete_stack(StackName=stackname)

if __name__=="__main__":
    try:
        init_stdout_logger(logging.INFO)
        argsconfig=yaml.load("""
        - name: config
          type: file
        - name: stage
          type: enum
          options:
          - dev
          - prod
        """, Loader=yaml.FullLoader)
        args=argsparse(sys.argv[1:], argsconfig)
        config=args.pop("config")
        config["globals"]["stage"]=args.pop("stage")
        stackname="%s-%s" % (config["globals"]["app"],
                             config["globals"]["stage"])
        delete_stack(stackname)
        waiter=CF.get_waiter("stack_delete_complete")
        waiter.wait(StackName=stackname)
    except ClientError as error:
        print (error)
    except WaiterError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
