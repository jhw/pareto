from pareto.components import *

@resource(suffix="action")
def Action(concurrency=None,
           handler="index.handler",
           memory=512,
           timeout=30,
           **kwargs):
    dlqarn=fn_getatt("%s-action-dead-letter-queue" % kwargs["name"], "Arn")
    rolearn=fn_getatt("%s-action-role" % kwargs["name"], "Arn")
    props={"Code": {"S3Bucket": kwargs["staging"]["bucket"],
                    "S3Key": kwargs["staging"]["key"]},
           "FunctionName": resource_name(kwargs),
           "Handler": handler,
           "MemorySize": memory,
           "DeadLetterConfig": {"TargetArn": dlqarn},                   
           "Role": rolearn,
           "Runtime": "python%s" % kwargs["runtime"],
           "Timeout": timeout}
    if concurrency:
        props["ReservedConcurrentExecutions"]=concurrency
    return "AWS::Lambda::Function", props

"""
- NB AWS::IAM::Role `RoleName` attribute isn't required
- however you do need a logical name for the role
- simplest to just use the parent resource name, which will get suffixed with `-action-arn` (see below)
- but this is only going to work if you have a single action per trigger
"""

def ActionRole(**kwargs):
    rolekwargs={}
    rolekwargs["name"]=kwargs["name"]
    rolekwargs["permissions"]=kwargs["action"]["permissions"]
    rolekwargs["service"]="lambda.amazonaws.com"
    return IamRole(**rolekwargs)

@resource(suffix="action-dead-letter-queue")
def ActionDeadLetterQueue(**kwargs):
    return "AWS::SQS::Queue"

@resource(suffix="action-version")
def ActionVersion(**kwargs):
    props={"FunctionName": ref("%s-action" % kwargs["name"])}
    return "AWS::Lambda::Version", props

@resource(suffix="action-event-config")
def ActionEventConfig(retries=0,
                        **kwargs):
    qualifier=fn_getatt("%s-action-version" % kwargs["name"], "Version")
    props={"FunctionName": ref("%s-action" % kwargs["name"]),
           "Qualifier": qualifier,
           "MaximumRetryAttempts": retries}
    return "AWS::Lambda::EventInvokeConfig", props

@resource(suffix="action-role")
def IamRole(**kwargs):
    def assume_role_policy_doc():
        statement=[{"Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Principal": {"Service": kwargs["service"]}}]
        return {"Statement": statement,
                "Version": "2012-10-17"}
    def policy(permissions):            
        statement=[{"Action": permission,
                    "Effect": "Allow",
                    "Resource": "*"}
                   for permission in permissions]
        return {"PolicyDocument": {"Statement": statement,
                                   "Version": "2012-10-17"},
                "PolicyName": random_name("inline-policy")} # "conditional"
    props={"AssumeRolePolicyDocument": assume_role_policy_doc()}
    if "permissions" in kwargs:
        props["Policies"]=[policy(kwargs["permissions"])]
    return "AWS::IAM::Role", props

if __name__=="__main__":
    pass
