from pareto.components import *

def synth_api(**kwargs):
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
    """
    - api-gw currently very bare bones and missing
      - resource
      - account + cw role
    - in order not to have too many api-gw resources and breach CF limit
    - see https://gist.github.com/jhw/fba6bed6637e784b735c57505d62bba8 for options
    """
    @resource(suffix="api-gw-rest-api")
    def ApiGwRestApi(**kwargs):
        props={"Name": random_name("rest-api")} # not 
        return "AWS::ApiGateway::RestApi", props
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
        arnpattern="arn:aws:apigateway:%s:lambda:path/2015-03-31/functions/${lambda_arn}/invocations"
        lambdaarn=fn_getatt(kwargs["name"], "Arn")
        uriparams={"lambda_arn": lambdaarn}
        uri=fn_sub(arnpattern % kwargs["region"],
                   uriparams)
        integration={"Uri": uri,
                     "IntegrationHttpMethod": "POST",
                     "Type": "AWS_PROXY"}
        restapi=ref("%s-api-gw-rest-api" % kwargs["name"])
        parent=fn_getatt("%s-api-gw-rest-api" % kwargs["name"],
                         "RootResourceId")
        props={"AuthorizationType": "NONE",
               "RestApiId": restapi,
               "ResourceId": parent,
               "HttpMethod": kwargs["method"],
               "Integration": integration}
        return "AWS::ApiGateway::Method", props
    @resource(suffix="api-gw-permission")
    def ApiGwPermission(**kwargs):
        arnpattern="arn:aws:execute-api:%s:${AWS::AccountId}:${rest_api}/${stage_name}/%s/"
        restapi=ref("%s-api-gw-rest-api" % kwargs["name"])
        stagename=ref("%s-api-gw-stage" % kwargs["name"])
        eventparams={"rest_api": restapi,
                     "stage_name": stagename}
        eventsource=fn_sub(arnpattern % (kwargs["region"],
                                         kwargs["method"]),
                           eventparams)
        funcname=fn_getatt(kwargs["name"], "Arn")
        props={"Action": "lambda:InvokeFunction",
               "FunctionName": funcname,
               "Principal": "apigateway.amazonaws.com",
               "SourceArn": eventsource}
        return "AWS::Lambda::Permission", props
    @output(suffix="url")
    def ApiGwUrl(**kwargs):
        urlpattern="https://${rest_api}.execute-api.%s.${AWS::URLSuffix}/${stage_name}"
        url=urlpattern % kwargs["region"]
        restapi=ref("%s-api-gw-rest-api" % kwargs["name"])
        stagename=ref("%s-api-gw-stage" % kwargs["name"])
        urlparams={"rest_api": restapi,
                   "stage_name": stagename}
        return fn_sub(url, urlparams)
    template=Template(resources=[Function(**kwargs),
                                 FunctionRole(**kwargs),
                                 FunctionDeadLetterQueue(**kwargs),
                                 FunctionVersion(**kwargs),
                                 FunctionEventConfig(**kwargs)])
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