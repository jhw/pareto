#!/usr/bin/env python

from pareto.scripts import *

from pareto.scripts.helpers.resources import Resources

def empty_bucket(s3, bucketname):
    try:
        paginator=s3.get_paginator("list_objects_v2")
        pages=paginator.paginate(Bucket=bucketname)
        for struct in pages:
            if "Contents" in struct:
                for obj in struct["Contents"]:
                    logging.info("deleting object %s" % obj["Key"])
                    s3.delete_object(Bucket=bucketname,
                                     Key=obj["Key"])
    except ClientError as error:
        if error.response["Error"]["Code"] not in ["NoSuchBucket"]:
            raise error

def detach_policies(iam, rolename):
    try:
        for policy in iam.list_attached_role_policies(RoleName=rolename)["AttachedPolicies"]:
            logging.info("detaching policy %s" % policy["PolicyArn"])
            iam.detach_role_policy(RoleName=rolename,
                                   PolicyArn=policy["PolicyArn"])
    except ClientError as error:
        if error.response["Error"]["Code"] not in ["NoSuchEntity"]:
            raise error
            
def delete_stack(s3, iam, cf, stackname):
    logging.info("deleting stack %s" % stackname)
    resources=Resources.initialise(stackname, cf)
    for resource in resources:
        if resource["ResourceType"]=="AWS::S3::Bucket":
            empty_bucket(s3, resource["PhysicalResourceId"])
        if resource["ResourceType"]=="AWS::IAM::Role":
            detach_policies(iam, resource["PhysicalResourceId"])
    cf.delete_stack(StackName=stackname)

if __name__=="__main__":
    try:
        init_stdout_logger(logging.INFO)
        argsconfig=yaml.safe_load("""
        - name: config
          type: file
        - name: stage
          type: enum
          options:
          - dev
          - prod
        """)
        args=argsparse(sys.argv[1:], argsconfig)
        config=args.pop("config")
        config["globals"]["stage"]=args.pop("stage")
        stackname="%s-%s" % (config["globals"]["app"],
                             config["globals"]["stage"])
        s3=boto3.client("s3")
        iam=boto3.client("iam")
        cf=boto3.client("cloudformation")
        delete_stack(s3, iam, cf, stackname)
        waiter=cf.get_waiter("stack_delete_complete")
        waiter.wait(StackName=stackname)
    except ClientError as error:
        print (error)
    except WaiterError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
