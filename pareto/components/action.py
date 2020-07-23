from pareto.components import *

def synth_action(**kwargs):
    @resource()
    def Function(concurrency=None,
                 handler="index.handler",
                 memory=512,
                 timeout=30,
                 **kwargs):
        dlqarn=fn_getatt("%s-dead-letter-queue" % kwargs["name"], "Arn")
        rolearn=fn_getatt("%s-role" % kwargs["name"], "Arn")
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
    @output(suffix="arn")
    def FunctionArn(**kwargs):
        return fn_getatt(kwargs["name"], "Arn")
    def FunctionRole(**kwargs):
        rolekwargs=dict(kwargs["iam"])
        rolekwargs["name"]=kwargs["name"]
        rolekwargs["service"]="lambda.amazonaws.com"
        return IamRole(**rolekwargs)
    @resource(suffix="dead-letter-queue")
    def FunctionDeadLetterQueue(**kwargs):
        return "AWS::SQS::Queue"
    @resource(suffix="version")
    def FunctionVersion(**kwargs):
        props={"FunctionName": ref(kwargs["name"])}
        return "AWS::Lambda::Version", props
    @resource(suffix="event-config")
    def FunctionEventConfig(retries=0,
                            **kwargs):
        qualifier=fn_getatt("%s-version" % kwargs["name"], "Version")
        props={"FunctionName": ref(kwargs["name"]),
               "Qualifier": qualifier,
               "MaximumRetryAttempts": retries}
        return "AWS::Lambda::EventInvokeConfig", props
    @resource(suffix="role")
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
    template=Template(resources=[Function(**kwargs),
                                 FunctionRole(**kwargs),
                                 FunctionDeadLetterQueue(**kwargs),
                                 FunctionVersion(**kwargs),
                                 FunctionEventConfig(**kwargs)],
                      outputs=[FunctionArn(**kwargs)])
    return template

if __name__=="__main__":
    pass
