from pareto.components import *

import random

"""
LambdaLayer:
    Properties:
      CompatibleRuntimes:
        - Ref: LambdaRuntime
      Content:
        S3Bucket: !Ref S3DeployBucket
        S3Key: !Ref S3LayerKey
      LayerName: !Sub "${AppName}-lambda-layer-${StageName}"
    Type: AWS::Lambda::LayerVersion
"""

def synth_function(**kwargs):
    @resource()
    def Function(concurrency=None,
                 handler="index.handler",
                 memory=512,
                 runtime="python3.7",
                 timeout=30,
                 **kwargs):
        dlqarn=fn_getatt("%s-dlq" % kwargs["name"], "Arn")
        rolearn=fn_getatt("%s-role" % kwargs["name"], "Arn")
        props={"Code": {"S3Bucket": kwargs["staging"]["bucket"],
                        "S3Key": kwargs["staging"]["key"]},
               "FunctionName": resource_id(**kwargs),
               "Handler": handler,
               "MemorySize": memory,
               "DeadLetterConfig": {"TargetArn": dlqarn},                   
               "Role": rolearn,
               "Runtime": runtime,
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
    @resource(suffix="dlq")
    def FunctionDeadLetterQueue(**kwargs):
        return "AWS::SQS::Queue", {}
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
    def Layer(kwargs, layer):
        suffix="%s-layer" % layer["name"]
        @resource(suffix=suffix)
        def Layer(**kwargs):
            return "AWS::Lambda::LayerVersion", {}
        return Layer(**kwargs)
    @resource(suffix="role")
    def IamRole(**kwargs):
        def assume_role_policy_doc():
            statement=[{"Action": "sts:AssumeRole",
                        "Effect": "Allow",
                        "Principal": {"Service": kwargs["service"]}}]
            return {"Statement": statement,
                    "Version": "2012-10-17"}
        """
        - policy name is required unfortunately
        - but no particular need to give it a meaningful name
        """
        def random_policy_name(n=32):
            salt="".join([chr(65+int(26*random.random()))
                          for i in range(n)])
            return "inline-policy-%s" % salt
        def policy(permissions):            
            statement=[{"Action": permission,
                        "Effect": "Allow",
                        "Resource": "*"}
                       for permission in permissions]
            return {"PolicyDocument": {"Statement": statement,
                                       "Version": "2012-10-17"},
                    "PolicyName": random_policy_name()}
        props={"AssumeRolePolicyDocument": assume_role_policy_doc()}
        if "permissions" in kwargs:
            props["Policies"]=[policy(kwargs["permissions"])]
        return "AWS::IAM::Role", props
    """
    - api-gw currently very bare bones and missing
      - resource
      - account + cw role
    - in order not to have too many api-gw resources and breach CF limit
    - see https://gist.github.com/jhw/fba6bed6637e784b735c57505d62bba8 for options
    """
    @resource(suffix="api-gw-rest-api")
    def ApiGwRestApi(**kwargs):
        return "AWS::ApiGateway::RestApi", {}
    @resource(suffix="api-gw-deployment")
    def ApiGwDeployment(**kwargs):
        restapi=ref("%s-api-gw-rest-api" % kwargs["name"])
        props={"RestApiId": restapi}
        method="%s-api-gw-method" % kwargs["name"]
        return "AWS::ApiGateway::Deployment", props, [method]
    @resource(suffix="api-gw-stage")
    def ApiGwStage(**kwargs):
        restapi=ref("%s-api-gw-rest-api" % kwargs["name"])
        deployment=ref("%s-api-gw-deployment" % kwargs["name"])
        props={"RestApiId": restapi,
               "DeploymentId": deployment,
               "StageName": kwargs["stage"]}
        return "AWS::ApiGateway::Stage", props
    @resource(suffix="api-gw-method")
    def ApiGwMethod(**kwargs):
        uri=fn_sub("arn:aws:apigateway:%s:lambda:path/2015-03-31/functions/${lambda_arn}/invocations" % kwargs["region"],
                   {"lambda_arn": fn_getatt(kwargs["name"], "Arn")})
        integration={"Uri": uri,
                     "IntegrationHttpMethod": "POST",
                     "Type": "AWS_PROXY"}
        restapi=ref("%s-api-gw-rest-api" % kwargs["name"])
        parent=fn_getatt("%s-api-gw-rest-api" % kwargs["name"],
                         "RootResourceId")
        props={"AuthorizationType": "NONE",
               "RestApiId": restapi,
               "ResourceId": parent,
               "HttpMethod": kwargs["api"]["method"],
               "Integration": integration}
        return "AWS::ApiGateway::Method", props
    @resource(suffix="api-gw-permission")
    def ApiGwPermission(**kwargs):
        eventsource=fn_sub("arn:aws:execute-api:%s:${AWS::AccountId}:${rest_api}/%s/%s/" % (kwargs["region"], kwargs["stage"], kwargs["api"]["method"]),
                           {"rest_api": ref("%s-api-gw-rest-api" % kwargs["name"])})
        funcname=fn_getatt(kwargs["name"], "Arn")
        props={"Action": "lambda:InvokeFunction",
               "FunctionName": funcname,
               "Principal": "apigateway.amazonaws.com",
               "SourceArn": eventsource}
        return "AWS::Lambda::Permission", props
    @output(suffix="url")
    def ApiGwUrl(**kwargs):
        url="https://${rest_api}.execute-api.%s.${AWS::URLSuffix}/%s" % (kwargs["region"], kwargs["stage"])
        restapi=ref("%s-api-gw-rest-api" % kwargs["name"])
        return fn_sub(url, {"rest_api": restapi})
    template=Template(resources=[Function(**kwargs),
                                 FunctionRole(**kwargs),
                                 FunctionDeadLetterQueue(**kwargs),
                                 FunctionVersion(**kwargs),
                                 FunctionEventConfig(**kwargs)])
    if "layers" in kwargs:
        template["resources"]+=[Layer(kwargs, layer)
                                for layer in kwargs["layers"]]
    if "api" in kwargs:
        template["resources"]+=[ApiGwRestApi(**kwargs),
                                ApiGwDeployment(**kwargs),
                                ApiGwStage(**kwargs),
                                ApiGwMethod(**kwargs),
                                ApiGwPermission(**kwargs)]
        template["outputs"].append(ApiGwUrl(**kwargs))
    else:
        template["outputs"].append(FunctionArn(**kwargs))
    return template

if __name__=="__main__":
    pass
