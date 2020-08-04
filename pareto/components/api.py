from pareto.components import *

InvokeArn="arn:aws:apigateway:%s:lambda:path/2015-03-31/functions/${lambda_arn}/invocations"

Arn="arn:aws:execute-api:%s:${AWS::AccountId}:${rest_api}/${stage_name}/%s/"

Url="https://${rest_api}.execute-api.%s.${AWS::URLSuffix}/${stage_name}"

@resource(suffix="api")
def ApiRoot(**kwargs):
    props={"Name": random_name("api")} # NB
    return "AWS::ApiGateway::RestApi", props

@resource(suffix="deployment")
def ApiDeployment(**kwargs):
    restapi=ref("%s-api" % kwargs["name"])
    props={"RestApiId": restapi}
    method="%s-method" % kwargs["name"]
    return "AWS::ApiGateway::Deployment", props, [method]

@resource(suffix="stage")
def ApiStage(**kwargs):
    restapi=ref("%s-api" % kwargs["name"])
    deployment=ref("%s-deployment" % kwargs["name"])
    props={"RestApiId": restapi,
           "DeploymentId": deployment,
           "StageName": kwargs["stage"]}
    return "AWS::ApiGateway::Stage", props

@resource(suffix="method")
def ApiMethod(**kwargs):
    target=ref("%s-arn" % kwargs["action"])
    uriparams={"lambda_arn": target}
    uri=fn_sub(InvokeArn % kwargs["region"],
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
def ApiPermission(**kwargs):
    restapi=ref("%s-api" % kwargs["name"])
    stagename=ref("%s-stage" % kwargs["name"])
    eventparams={"rest_api": restapi,
                 "stage_name": stagename}
    source=fn_sub(Arn % (kwargs["region"],
                         kwargs["method"]),
                  eventparams)
    target=ref("%s-arn" % kwargs["action"])
    props={"Action": "lambda:InvokeFunction",
           "FunctionName": target,
           "Principal": "apigateway.amazonaws.com",
           "SourceArn": source}
    return "AWS::Lambda::Permission", props

@output(suffix="url")
def ApiUrl(**kwargs):
    url=Url % kwargs["region"]
    restapi=ref("%s-api" % kwargs["name"])
    stagename=ref("%s-stage" % kwargs["name"])
    urlparams={"rest_api": restapi,
               "stage_name": stagename}
    return fn_sub(url, urlparams)

def synth_api(**kwargs):
    template=Template(resources=[ApiRoot(**kwargs),
                                 ApiDeployment(**kwargs),
                                 ApiStage(**kwargs),
                                 ApiMethod(**kwargs)],
                      outputs=[ApiUrl(**kwargs)])
    if "action" in kwargs:
        template.parameters.append(parameter("%s-arn" % kwargs["action"]))
        template.resources.append(ApiPermission(**kwargs))
    return template

if __name__=="__main__":
    pass
