from pareto.components import *

from pareto.charts.action import ActionCharts

DefaultPermissions=yaml.load("""
- logs:CreateLogGroup
- logs:CreateLogStream
- logs:PutLogEvents                                          
- sqs:SendMessage # dead letter queue
""", Loader=yaml.FullLoader)

@resource(suffix="action")
def Action(concurrency=None,
           handler="index.handler",
           memory=512,
           timeout=30,
           **kwargs):
    dlqarn=fn_getatt("%s-action-dead-letter-queue" % kwargs["name"], "Arn")
    rolearn=fn_getatt("%s-action-role" % kwargs["name"], "Arn")
    props={"Code": {"S3Bucket": kwargs["staging"]["lambda"]["bucket"],
                    "S3Key": kwargs["staging"]["lambda"]["key"]},
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
def ActionRole(**kwargs):
    def assume_role_policy_doc():
        statement=[{"Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"}}]
        return {"Statement": statement,
                "Version": "2012-10-17"}
    def default_permissions(fn, defaults=DefaultPermissions):
        def wrapped(action):
            permissions=set(action["permissions"]) if "permissions" in action else set()
            permissions.update(defaults)
            return fn(list(permissions))
        return wrapped
    def assert_permissions(fn):
        def wrapped(permissions):
            wildcards=[permission
                       for permission in permissions
                       if permission.endswith(":*")]
            if wildcards!=[]:
                raise RuntimeError("IAM wildcards detected - %s" % ", ".join(wildcards))
            return fn(permissions)
        return wrapped        
    @default_permissions
    @assert_permissions
    def policy(permissions):            
        statement=[{"Action": permission,
                    "Effect": "Allow",
                    "Resource": "*"}
                   for permission in sorted(permissions)]
        return {"PolicyDocument": {"Statement": statement,
                                   "Version": "2012-10-17"},
                "PolicyName": random_name("inline-policy")} # "conditional"
    props={"AssumeRolePolicyDocument": assume_role_policy_doc()}
    props["Policies"]=[policy(kwargs["action"])]
    return "AWS::IAM::Role", props

def synth_action(template, **kwargs):
    template.resources+=[Action(**kwargs),
                         ActionRole(**kwargs),
                         ActionDeadLetterQueue(**kwargs),
                         ActionVersion(**kwargs),
                         ActionEventConfig(**kwargs)]
    if ("action" in kwargs and
        "layer" in kwargs["staging"]):
        for package in kwargs["staging"]["layer"]:
            print (package)
    template.dashboard+=[ActionCharts(**kwargs)]

if __name__=="__main__":
    pass
