#!/usr/bin/env python

from pareto.scripts import *

def clean_s3(s3, config):
    print ("--- s3 ---")
    paginator=s3.get_paginator("list_objects_v2")
    pages=paginator.paginate(Bucket=config["globals"]["bucket"],
                             Prefix=config["globals"]["app"])
    for struct in pages:
        if "Contents" in struct:
            for obj in struct["Contents"]:                    
                print ("deleting file %s" % obj["Key"])
                s3.delete_object(Bucket=config["globals"]["bucket"],
                                 Key=obj["Key"])                    

def clean_iam(iam,
              config,
              suffixes=["admin-role"]):
    print ("--- iam ---")
    def is_valid_suffix(rolename, suffixes):
        for suffix in suffixes:
            if rolename.endswith(suffix):
                return True
        return False
    def delete_policies(role):
        for policy in iam.list_attached_role_policies(RoleName=role["RoleName"])["AttachedPolicies"]:
            print ("detaching/deleting policy %s" % policy["PolicyName"])
            iam.detach_role_policy(RoleName=role["RoleName"],
                                   PolicyArn=policy["PolicyArn"])
            iam.delete_policy(PolicyArn=policy["PolicyArn"])
    for role in iam.list_roles()["Roles"]:
        if not (role["RoleName"].startswith(config["globals"]["app"]) and
                is_valid_suffix(role["RoleName"], suffixes)):
            continue
        delete_policies(role)
        print ("deleting role %s" % role["RoleName"])
        iam.delete_role(RoleName=role["RoleName"])

def clean_codebuild(cb, config):
    print ("--- codebuild ---")
    for projectname in cb.list_projects()["projects"]:
        if not projectname.startswith(config["globals"]["app"]):
            continue
        print ("deleting project %s" % projectname)
        cb.delete_project(name=projectname)
                
if __name__=="__main__":
    try:
        init_stdout_logger(logging.INFO)
        argsconfig=yaml.safe_load("""
        - name: config
          type: file
        """)
        args=argsparse(sys.argv[1:], argsconfig)
        for service in ["s3",
                        "iam",
                        "codebuild"]:            
            fn=eval("clean_%s" % service)
            client=boto3.client(service)
            fn(client, args["config"])
    except ClientError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
