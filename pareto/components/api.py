from pareto.components import *

from pareto.components.function import *

def synth_api(**kwargs):
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
