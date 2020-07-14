"""
- https://stackoverflow.com/questions/44121532/how-to-create-aws-iam-role-attaching-managed-policy-only-using-boto3
"""

from pareto.scripts import *

import boto3, yaml

IAM=boto3.client("iam")

AdminAccessArn="arn:aws:iam::aws:policy/AdministratorAccess"

CBPolicyDoc=yaml.load("""
Statement:
  - Action: sts:AssumeRole
    Effect: Allow
    Principal:
      Service: codebuild.amazonaws.com
Version: '2012-10-17'
""", Loader=yaml.FullLoader)

def create_role(config,
                adminarn=AdminAccessArn,
                policydoc=CBPolicyDoc):
    rolename="%s-admin-role" % config["globals"]["app"]
    role=IAM.create_role(RoleName=rolename,
                         AssumeRolePolicyDocument=json.dumps(policydoc))
    IAM.attach_role_policy(RoleName=rolename,
                           PolicyArn=adminarn)
    return role["Role"]["Arn"]

if __name__=="__main__":
    try:
        init_stdout_logger(logging.INFO)
        argsconfig=yaml.load("""
        - name: config
          type: file
        """, Loader=yaml.FullLoader)
        args=argsparse(sys.argv[1:], argsconfig)
        config=args.pop("config")
        # print (create_role(config))
        print ([role["RoleName"]
                for role in IAM.list_roles()["Roles"]])
    except ClientError as error:
        logging.error(str(error))
    except RuntimeError as error:
        logging.error(str(error))

