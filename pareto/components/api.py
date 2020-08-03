"""
- api-gw currently very bare bones and missing
  - resource
  - account + cw role
- in order not to have too many api-gw resources and breach CF limit
- see https://gist.github.com/jhw/fba6bed6637e784b735c57505d62bba8 for options
"""

from pareto.components import *

@resource(suffix="api")
def ApiGwRestApi(**kwargs):
    props={"Name": random_name("api")} # note
    return "AWS::ApiGateway::RestApi", props

@resource(suffix="deployment")
def ApiGwDeployment(**kwargs):
    restapi=ref("%s-api" % kwargs["name"])
    props={"RestApiId": restapi}
    method="%s-method" % kwargs["name"]
    return "AWS::ApiGateway::Deployment", props, [method]

@resource(suffix="stage")
def ApiGwStage(**kwargs):
    restapi=ref("%s-api" % kwargs["name"])
    deployment=ref("%s-deployment" % kwargs["name"])
    props={"RestApiId": restapi,
           "DeploymentId": deployment,
           "StageName": kwargs["stage"]}
    return "AWS::ApiGateway::Stage", props

@resource(suffix="method")
def ApiGwMethod(**kwargs):
    arnpattern="arn:aws:apigateway:%s:lambda:path/2015-03-31/functions/${lambda_arn}/invocations"
    funcarn=fn_getatt(kwargs["action"], "Arn")
    uriparams={"lambda_arn": funcarn}
    uri=fn_sub(arnpattern % kwargs["region"],
               uriparams)
    integration={"Uri": uri,
                 "IntegrationHttpMethod": "POST",
                 "Type": "AWS_PROXY"}
    restapi=ref("%s-api" % kwargs["name"])
    parent=fn_getatt("%s-api" % kwargs["name"],
                     "RootResourceId")
    props={"AuthorizationType": "NONE",
           "RestApiId": restapi,
           "ResourceId": parent,
           "HttpMethod": kwargs["method"],
           "Integration": integration}
    return "AWS::ApiGateway::Method", props

@resource(suffix="permission")
def ApiGwPermission(**kwargs):
    arnpattern="arn:aws:execute-api:%s:${AWS::AccountId}:${rest_api}/${stage_name}/%s/"
    restapi=ref("%s-api" % kwargs["name"])
    stagename=ref("%s-stage" % kwargs["name"])
    eventparams={"rest_api": restapi,
                 "stage_name": stagename}
    source=fn_sub(arnpattern % (kwargs["region"],
                                     kwargs["method"]),
                       eventparams)
    funcarn=fn_getatt(kwargs["action"], "Arn")
    props={"Action": "lambda:InvokeFunction",
           "FunctionName": funcarn,
           "Principal": "apigateway.amazonaws.com",
           "SourceArn": source}
    return "AWS::Lambda::Permission", props

@output(suffix="url")
def ApiGwUrl(**kwargs):
    urlpattern="https://${rest_api}.execute-api.%s.${AWS::URLSuffix}/${stage_name}"
    url=urlpattern % kwargs["region"]
    restapi=ref("%s-api" % kwargs["name"])
    stagename=ref("%s-stage" % kwargs["name"])
    urlparams={"rest_api": restapi,
               "stage_name": stagename}
    return fn_sub(url, urlparams)

def synth_api(**kwargs):
    return Template(resources=[ApiGwRestApi(**kwargs),
                               ApiGwDeployment(**kwargs),
                               ApiGwStage(**kwargs),
                               ApiGwMethod(**kwargs),
                               ApiGwPermission(**kwargs)],
                    outputs=[ApiGwUrl(**kwargs)])

if __name__=="__main__":
    pass
