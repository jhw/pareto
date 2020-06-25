from pareto.components import *

def synth_function(**kwargs):
    @resource()
    def Function(concurrency=None,
                 handler="index.handler",
                 memory=512,
                 runtime="python3.7",
                 timeout=30,
                 **kwargs):
        props={"Code": {"S3Bucket": kwargs["staging"]["bucket"],
                        "S3Key": kwargs["staging"]["key"]},
               "FunctionName": global_name(kwargs),
               "Handler": handler,
               "MemorySize": memory,
               "Role": fn_getatt("%s-role" % kwargs["name"], "Arn"),
               "Runtime": runtime,
               "Timeout": timeout}
        if concurrency:
            props["ReservedConcurrentExecutions"]=concurrency
        return "AWS::Lambda::Function", props
    def FunctionRole(**kwargs):
        rolekwargs=dict(kwargs["iam"])
        rolekwargs["name"]=kwargs["name"]
        rolekwargs["service"]="lambda.amazonaws.com"
        return IamRole(**rolekwargs)
    """
    - api-gw currently very bare bones and missing
      - resource
      - account + cw role
    - in order not to have too many api-gw resources and breach CF limit
    - see https://gist.github.com/jhw/fba6bed6637e784b735c57505d62bba8 for options
    """
    @resource(suffix="api-gw-rest-api")
    def ApiGwRestApi(**kwargs):
        name="%s-api-gw-rest-api" % kwargs["name"]
        props={"Name": name}
        return "AWS::ApiGateway::RestApi", props
    @resource(suffix="api-gw-deployment")
    def ApiGwDeployment(**kwargs):
        restapi=ref("%s-api-gw-rest-api" % kwargs["name"])
        method=hungarorise("%s-api-gw-method" % kwargs["name"])
        props, depends = {"RestApiId": restapi}, [method]
        return "AWS::ApiGateway::Deployment", props,  depends
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
        uri=fn_sub("arn:${AWS::Partition}:apigateway:%s:lambda:path/2015-03-31/functions/${lambda_arn}/invocations" % kwargs["region"],
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
        sourcearn="arn:${AWS::Partition}:execute-api:%s:${AWS::AccountId}:${rest_api}/%s/%s/" % (kwargs["region"], kwargs["stage"], kwargs["api"]["method"])
        restapi=ref("%s-api-gw-rest-api" % kwargs["name"])
        eventsource=fn_sub(sourcearn, {"rest_api": restapi})
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
    resources=[Function(**kwargs),
               FunctionRole(**kwargs)]
    outputs=[]
    if "api" in kwargs:
        resources+=[ApiGwRestApi(**kwargs),
                    ApiGwDeployment(**kwargs),
                    ApiGwStage(**kwargs),
                    ApiGwMethod(**kwargs),
                    ApiGwPermission(**kwargs)]
        outputs.append(ApiGwUrl(**kwargs))
    return {"resources": resources,
            "outputs": outputs}

if __name__=="__main__":
    pass
