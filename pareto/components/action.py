from pareto.components import *

from pareto.components.role import IAMRole, DefaultRolePolicyDoc

from pareto.charts.action import ActionCharts

from pareto.helpers.text import underscore

DefaultPermissions=yaml.safe_load("""
- logs:CreateLogGroup
- logs:CreateLogStream
- logs:PutLogEvents                                          
- sqs:SendMessage # dead letter queue
""")

ParamNames=yaml.safe_load("""
- app-name
- stage-name
- staging-bucket
- lambda-staging-key
- runtime-version
- region # required by charts
""")

MaxRetries=2 # 2 is max

@resource()
def Action(concurrency=None,
           handlerpat="${app_name}/%s/index.handler", # NB
           memory=128,
           timeout=30,
           **kwargs):
    dlqarn=fn_getatt("%s-dead-letter-queue" % kwargs["name"], "Arn")
    rolearn=fn_getatt("%s-role" % kwargs["name"], "Arn")
    handler=fn_sub(handlerpat % underscore(kwargs["name"]),
                   {"app_name": ref("app-name")})
    props={"Code": {"S3Bucket": ref("staging-bucket"),
                    "S3Key": ref("lambda-staging-key")},
           "FunctionName": resource_name(kwargs),
           "Handler": handler,
           "MemorySize": memory,
           "DeadLetterConfig": {"TargetArn": dlqarn},                   
           "Role": rolearn,
           "Runtime": fn_sub("python${version}",
                             {"version": ref("runtime-version")}),
           "Timeout": timeout}
    if "layers" in kwargs:
        props["Layers"]=[ref("%s-layer-arn" % layername)
                         for layername in kwargs["layers"]]
    if concurrency:
        props["ReservedConcurrentExecutions"]=concurrency
    return "AWS::Lambda::Function", props

@resource(suffix="dead-letter-queue")
def ActionDeadLetterQueue(**kwargs):
    return "AWS::SQS::Queue", {}

@resource(suffix="version")
def ActionVersion(**kwargs):
    props={"FunctionName": ref(kwargs["name"])}
    return "AWS::Lambda::Version", props

@resource(suffix="event-config")
def ActionEventConfig(retries=MaxRetries,
                      **kwargs):
    qualifier=fn_getatt("%s-version" % kwargs["name"], "Version")
    props={"FunctionName": ref(kwargs["name"]),
           "Qualifier": qualifier,
           "MaximumRetryAttempts": retries}
    return "AWS::Lambda::EventInvokeConfig", props

@resource(suffix="role")
def ActionRole(**kwargs):
    def role_policy_doc():
        return DefaultRolePolicyDoc("lambda.amazonaws.com")
    return IAMRole(rolepolicyfn=role_policy_doc,
                   defaults=DefaultPermissions,
                   **kwargs)

@output(suffix="arn")
def ActionArn(**kwargs):
    return fn_getatt(kwargs["name"], "Arn")

def synth_action(template, **kwargs):
    template.update(Parameters=[parameter(paramname)
                                for paramname in ParamNames],
                    Resources=[Action(**kwargs),
                               ActionRole(**kwargs),
                               ActionDeadLetterQueue(**kwargs),
                               ActionVersion(**kwargs),
                               ActionEventConfig(**kwargs)],
                    Charts=ActionCharts(**kwargs),
                    Outputs=ActionArn(**kwargs))
    if "layers" in kwargs:
        for layername in kwargs["layers"]:
            template.update(Parameters=parameter("%s-layer-arn" % layername))

if __name__=="__main__":
    pass
