from pareto.components import *

LambdaInvokeArn="arn:aws:apigateway:%s:lambda:path/2015-03-31/functions/${lambda_arn}/invocations"

"""
- https://docs.aws.amazon.com/apigateway/latest/developerguide/arn-format-reference.html
"""

ExecuteApiArn="arn:aws:execute-api:%s:${AWS::AccountId}:${rest_api}/${stage_name}/%s/%s"

Url="https://${rest_api}.execute-api.%s.${AWS::URLSuffix}/${stage_name}/%s"

@resource(suffix="root")
def ApiRoot(**kwargs):
    props={"Name": random_id("rest-api")} # NB
    return "AWS::ApiGateway::RestApi", props

@resource(suffix="deployment")
def ApiDeployment(**kwargs):
    root=ref("%s-root" % kwargs["name"])
    props={"RestApiId": root}
    depends=["%s-%s-%s" % (kwargs["name"],
                           resource["name"],
                           suffix)
             for resource in kwargs["resources"]
             for suffix in ["method", "cors-options"]]
    return "AWS::ApiGateway::Deployment", props, depends

@resource(suffix="stage")
def ApiStage(**kwargs):
    root=ref("%s-root" % kwargs["name"])
    deployment=ref("%s-deployment" % kwargs["name"])
    props={"DeploymentId": deployment,
           "RestApiId": root,           
           "StageName": kwargs["stage"]}
    return "AWS::ApiGateway::Stage", props

def ApiResource(endpoint, **kwargs):
    suffix="%s-resource" % endpoint["name"]
    @resource(suffix=suffix)
    def ApiResource(endpoint, **kwargs):
        root=ref("%s-root" % kwargs["name"])
        parent=fn_getatt("%s-root" % kwargs["name"],
                         "RootResourceId")
        props={"ParentId": parent,
               "RestApiId": root,
               "PathPart": endpoint["name"]}
        return "AWS::ApiGateway::Resource", props
    return ApiResource(endpoint, **kwargs)

def ApiMethod(endpoint, **kwargs):
    suffix="%s-method" % endpoint["name"]
    @resource(suffix=suffix)
    def ApiMethod(endpoint, **kwargs):
        target=ref("%s-arn" % endpoint["action"])
        uri=fn_sub(LambdaInvokeArn % kwargs["region"],
                   {"lambda_arn": target})
        integration={"Uri": uri,
                     "IntegrationHttpMethod": "POST",
                     "Type": "AWS_PROXY"}
        root=ref("%s-root" % kwargs["name"])
        parent=ref("%s-%s-resource" % (kwargs["name"],
                                       endpoint["name"]))
        props={"AuthorizationType": "NONE",
               "RestApiId": root,
               "ResourceId": parent,
               "HttpMethod": endpoint["method"],
               "Integration": integration}
        return "AWS::ApiGateway::Method", props
    return ApiMethod(endpoint, **kwargs)

def ApiCorsOptions(endpoint, **kwargs):
    suffix="%s-cors-options" % endpoint["name"]
    @resource(suffix=suffix)
    def ApiCorsOptions(endpoint, **kwargs):
        props={}
        return "AWS::ApiGateway::Method", props
    return ApiCorsOptions(endpoint, **kwargs)

def ApiPermission(endpoint, **kwargs):
    suffix="%s-permission" % endpoint["name"]
    @resource(suffix=suffix)
    def ApiPermission(endpoint, **kwargs):
        root=ref("%s-root" % kwargs["name"])
        stage=ref("%s-stage" % kwargs["name"])
        source=fn_sub(ExecuteApiArn % (kwargs["region"],
                                       endpoint["method"],
                                       endpoint["name"]),
                      {"rest_api": root,
                       "stage_name": stage})
        target=ref("%s-arn" % endpoint["action"])
        props={"Action": "lambda:InvokeFunction",
               "FunctionName": target,
               "Principal": "apigateway.amazonaws.com",
               "SourceArn": source}
        return "AWS::Lambda::Permission", props
    return ApiPermission(endpoint, **kwargs)

def ApiUrl(endpoint, **kwargs):
    suffix="%s-url" % endpoint["name"]
    @output(suffix=suffix)
    def ApiUrl(endpoint, **kwargs):
        root=ref("%s-root" % kwargs["name"])
        stage=ref("%s-stage" % kwargs["name"])
        return fn_sub(Url % (kwargs["region"],
                             endpoint["name"]),
                      {"rest_api": root,
                       "stage_name": stage})
    return ApiUrl(endpoint, **kwargs)

def synth_api(**kwargs):
    template=Template(resources=[ApiRoot(**kwargs),
                                 ApiDeployment(**kwargs),
                                 ApiStage(**kwargs)])
    for endpoint in kwargs["resources"]:
        template.parameters.append(parameter("%s-arn" % endpoint["action"]))
        template.resources+=[ApiResource(endpoint, **kwargs),
                             ApiMethod(endpoint, **kwargs),
                             ApiCorsOptions(endpoint, **kwargs),
                             ApiPermission(endpoint, **kwargs)]
        template.outputs.append(ApiUrl(endpoint, **kwargs))
    return template

if __name__=="__main__":
    pass
