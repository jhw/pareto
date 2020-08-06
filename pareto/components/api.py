from pareto.components import *

LambdaInvokeArn="arn:aws:apigateway:%s:lambda:path/2015-03-31/functions/${lambda_arn}/invocations"

"""
- https://docs.aws.amazon.com/apigateway/latest/developerguide/arn-format-reference.html
"""

ExecuteApiArn="arn:aws:execute-api:%s:${AWS::AccountId}:${rest_api}/${stage_name}/%s/%s"

Url="https://${rest_api}.execute-api.%s.${AWS::URLSuffix}/${stage_name}/%s"

PathPart="hello"

@resource(suffix="api")
def ApiRoot(**kwargs):
    props={"Name": random_id("rest-api")} # NB
    return "AWS::ApiGateway::RestApi", props

@resource(suffix="deployment")
def ApiDeployment(**kwargs):
    api=ref("%s-api" % kwargs["name"])
    props={"RestApiId": api}
    depends=[pat % kwargs["name"]
             for pat in ["%s-method"]]
    return "AWS::ApiGateway::Deployment", props, depends

@resource(suffix="stage")
def ApiStage(**kwargs):
    api=ref("%s-api" % kwargs["name"])
    deployment=ref("%s-deployment" % kwargs["name"])
    props={"DeploymentId": deployment,
           "RestApiId": api,           
           "StageName": kwargs["stage"]}
    return "AWS::ApiGateway::Stage", props

@resource(suffix="resource")
def ApiResource(**kwargs):
    api=ref("%s-api" % kwargs["name"])
    resource=fn_getatt("%s-api" % kwargs["name"],
                       "RootResourceId")
    props={"ParentId": resource,
           "RestApiId": api,
           "PathPart": PathPart}
    return "AWS::ApiGateway::Resource", props

@resource(suffix="method")
def ApiMethod(**kwargs):
    target=ref("%s-arn" % kwargs["action"])
    uri=fn_sub(LambdaInvokeArn % kwargs["region"],
               {"lambda_arn": target})
    integration={"Uri": uri,
                 "IntegrationHttpMethod": "POST",
                 "Type": "AWS_PROXY"}
    api=ref("%s-api" % kwargs["name"])
    resource=ref("%s-resource" % kwargs["name"])
    props={"AuthorizationType": "NONE",
           "RestApiId": api,
           "ResourceId": resource,
           "HttpMethod": kwargs["method"],
           "Integration": integration}
    return "AWS::ApiGateway::Method", props

@resource(suffix="permission")
def ApiPermission(**kwargs):
    api=ref("%s-api" % kwargs["name"])
    stage=ref("%s-stage" % kwargs["name"])
    source=fn_sub(ExecuteApiArn % (kwargs["region"],
                                   kwargs["method"],
                                   PathPart),
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
    return fn_sub(Url % (kwargs["region"],
                         PathPart),
                  {"rest_api": api,
                   "stage_name": stage})

def synth_api(**kwargs):
    template=Template(resources=[ApiRoot(**kwargs),
                                 ApiDeployment(**kwargs),
                                 ApiStage(**kwargs),
                                 ApiResource(**kwargs),
                                 ApiMethod(**kwargs)],
                      outputs=[ApiUrl(**kwargs)])
    if "action" in kwargs:
        template.parameters.append(parameter("%s-arn" % kwargs["action"]))
        template.resources.append(ApiPermission(**kwargs))
    return template

if __name__=="__main__":
    pass
