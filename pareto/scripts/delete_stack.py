#!/usr/bin/env python

from pareto.scripts import *

CF=boto3.client("cloudformation")
S3=boto3.client("s3")
IAM=boto3.client("iam")

def empty_bucket(bucketname):
    paginator=S3.get_paginator("list_objects_v2")
    pages=paginator.paginate(Bucket=bucketname)
    for struct in pages:
        if "Contents" in struct:
            for obj in struct["Contents"]:
                S3.delete_object(Bucket=bucketname,
                                 Key=obj["Key"])

def detach_policies(rolename):
    for policy in IAM.list_attached_role_policies(RoleName=rolename)["AttachedPolicies"]:
        IAM.detach_role_policy(RoleName=rolename,
                               PolicyArn=policy["PolicyArn"])
    
def delete_stack(stackname):
    resources=CF.describe_stack_resources(StackName=stackname)["StackResources"]
    for resource in resources:
        if resource["ResourceType"]=="AWS::S3::Bucket":
            empty_bucket(resource["PhysicalResourceId"])
        if resource["ResourceType"]=="AWS::IAM::Role":
            detach_policies(resource["PhysicalResourceId"])
    CF.delete_stack(StackName=stackname)

if __name__=="__main__":
    try:
        if len(sys.argv) < 2:
            raise RuntimeError("Please enter stage name")
        stagename=sys.argv[1]
        if stagename not in ["dev", "prod"]:
            raise RuntimeError("Stage name is invalid")
        stackname="%s-%s" % (Config["AppName"],
                             stagename)
        delete_stack(stackname)
        waiter=CF.get_waiter("stack_delete_complete")
        waiter.wait(StackName=stackname)
    except ClientError as error:
        print (error)
    except WaiterError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
