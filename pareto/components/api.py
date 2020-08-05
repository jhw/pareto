from pareto.components import *

InvokeArn="arn:aws:apigateway:%s:lambda:path/2015-03-31/functions/${lambda_arn}/invocations"

Arn="arn:aws:execute-api:%s:${AWS::AccountId}:${rest_api}/${stage_name}/%s/"

Url="https://${rest_api}.execute-api.%s.${AWS::URLSuffix}/${stage_name}"

@resource(suffix="api")
def ApiRoot(**kwargs):
    props={"Name": random_id("rest-api")} # NB
    return "AWS::ApiGateway::RestApi", props

@resource(suffix="deployment")
def ApiDeployment(**kwargs):
    api=ref("%s-api" % kwargs["name"])
    props={"RestApiId": api}
    method="%s-method" % kwargs["name"]
    return "AWS::ApiGateway::Deployment", props, [method]

@resource(suffix="stage")
def ApiStage(**kwargs):
    api=ref("%s-api" % kwargs["name"])
    deployment=ref("%s-deployment" % kwargs["name"])
    props={"RestApiId": api,
           "DeploymentId": deployment,
           "StageName": kwargs["stage"]}
    return "AWS::ApiGateway::Stage", props

@resource(suffix="method")
def ApiMethod(**kwargs):
    target=ref("%s-arn" % kwargs["action"])
    uri=fn_sub(InvokeArn % kwargs["region"],
               {"lambda_arn": target})
    integration={"Uri": uri,
                 "IntegrationHttpMethod": "POST",
                 "Type": "AWS_PROXY"}
    api=ref("%s-api" % kwargs["name"])
    parent=fn_getatt("%s-api" % kwargs["name"],
                     "RootResourceId")
    props={"AuthorizationType": "NONE",
           "RestApiId": api,
           "ResourceId": parent,
           "HttpMethod": kwargs["method"],
           "Integration": integration}
    return "AWS::ApiGateway::Method", props

@resource(suffix="permission")
def ApiPermission(**kwargs):
    api=ref("%s-api" % kwargs["name"])
    stage=ref("%s-stage" % kwargs["name"])
    source=fn_sub(Arn % (kwargs["region"],
                         kwargs["method"]),
                  {"rest_api": api,
                   "stage_name": stage})
    target=ref("%s-arn" % kwargs["action"])
    props={"Action": "lambda:InvokeFunction",
           "FunctionName": target,
           "Principal": "apigateway.amazonaws.com",
           "SourceArn": source}
    return "AWS::Lambda::Permission", props

@output(suffix="url")
def ApiUrl(**kwargs):
    api=ref("%s-api" % kwargs["name"])
    stage=ref("%s-stage" % kwargs["name"])
    return fn_sub(Url % kwargs["region"],
                  {"rest_api": api,
                   "stage_name": stage})

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
