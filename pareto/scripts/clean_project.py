#!/usr/bin/env python

from pareto.scripts import *

def clean_s3(config):
    print ("--- s3 ---")
    paginator=S3.get_paginator("list_objects_v2")
    pages=paginator.paginate(Bucket=config["globals"]["bucket"],
                             Prefix=config["globals"]["app"])
    for struct in pages:
        if "Contents" in struct:
            for obj in struct["Contents"]:                    
                print ("deleting file %s" % obj["Key"])
                S3.delete_object(Bucket=config["globals"]["bucket"],
                                 Key=obj["Key"])                    

def clean_iam(config,
              suffixes=["admin-role"]):
    print ("--- iam ---")
    def is_valid_suffix(rolename, suffixes):
        for suffix in suffixes:
            if rolename.endswith(suffix):
                return True
        return False
    def delete_policies(role):
        for policy in IAM.list_attached_role_policies(RoleName=role["RoleName"])["AttachedPolicies"]:
            print ("detaching/deleting policy %s" % policy["PolicyName"])
            IAM.detach_role_policy(RoleName=role["RoleName"],
                                   PolicyArn=policy["PolicyArn"])
            IAM.delete_policy(PolicyArn=policy["PolicyArn"])
    for role in IAM.list_roles()["Roles"]:
        if not (role["RoleName"].startswith(config["globals"]["app"]) and
                is_valid_suffix(role["RoleName"], suffixes)):
            continue
        delete_policies(role)
        print ("deleting role %s" % role["RoleName"])
        IAM.delete_role(RoleName=role["RoleName"])

def clean_codebuild(config):
    print ("--- codebuild ---")
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
        for fn in [clean_s3,
                   clean_iam,
                   clean_codebuild]:
            fn(args["config"])
    except ClientError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
