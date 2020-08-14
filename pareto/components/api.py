from pareto.components import *

from jsonschema import Draft7Validator

Draft7Schema="http://json-schema.org/draft-07/schema#"

LambdaInvokeArn="arn:aws:apigateway:%s:lambda:path/2015-03-31/functions/${lambda_arn}/invocations"

"""
- https://docs.aws.amazon.com/apigateway/latest/developerguide/arn-format-reference.html
"""

ExecuteApiArn="arn:aws:execute-api:%s:${AWS::AccountId}:${rest_api}/${stage_name}/%s/%s"

Url="https://${rest_api}.execute-api.%s.${AWS::URLSuffix}/${stage_name}/%s"

CorsHeaderPath="method.response.header.Access-Control-Allow-%s"

CorsHeaders=yaml.safe_load("""
- Content-Type
- X-Amz-Date
- Authorization
- X-Api-Key
- X-Amz-Security-Token
""")

LogsPermissions=yaml.safe_load("""
- logs:CreateLogGroup
- logs:CreateLogStream
- logs:DescribeLogGroups
- logs:DescribeLogStreams
- logs:PutLogEvents
- logs:GetLogEvents
- logs:FilterLogEvents
""")

@resource(suffix="root")
def ApiRoot(**kwargs):
    props={"Name": random_id("rest-api")} # NB
    return "AWS::ApiGateway::RestApi", props

@resource(suffix="account")
def ApiAccount(**kwargs):
    logsrole=fn_getatt("%s-logs-role" % kwargs["name"],
                       "Arn")
    props={"CloudWatchRoleArn": logsrole}
    depends=["%s-root" % kwargs["name"]]
    return "AWS::ApiGateway::Account", props, depends

@resource(suffix="logs-role")
def ApiLogsRole(**kwargs):
    def assume_role_policy_doc():
        statement=[{"Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Principal": {"Service": "apigateway.amazonaws.com"}}]
        return {"Statement": statement,
                "Version": "2012-10-17"}
    def policy(permissions=LogsPermissions):            
        statement=[{"Action": permission,
                    "Effect": "Allow",
                    "Resource": "*"}
                   for permission in sorted(permissions)]
        return {"PolicyDocument": {"Statement": statement,
                                   "Version": "2012-10-17"},
                "PolicyName": random_id("inline-policy")}
    props={"AssumeRolePolicyDocument": assume_role_policy_doc()}
    props["Policies"]=[policy()]
    return "AWS::IAM::Role", props

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

def ApiValidator(endpoint, **kwargs):
    suffix="%s-validator" % endpoint["name"]
    def assert_post_schema(fn):
        def wrapped(endpoint, **kwargs):
            if (endpoint["method"]=="GET" and
                "schema" in endpoint):
                raise RuntimeError("schema not supported for GET methods")
            return fn(endpoint, **kwargs)
        return wrapped
    @assert_post_schema    
    @resource(suffix=suffix)
    def ApiValidator(endpoint, **kwargs):
        root=ref("%s-root" % kwargs["name"])
        props={"RestApiId": root}
        if "params" in endpoint:
            props["ValidateRequestParameters"]=True
        if "schema" in endpoint:
            props["ValidateRequestBody"]=True
        return "AWS::ApiGateway::RequestValidator", props
    return ApiValidator(endpoint, **kwargs)

def ApiModel(endpoint, **kwargs):
    suffix="%s-model" % endpoint["name"]
    def validate_schema(fn):
        def wrapped(endpoint, **kwargs):
            try:
                Draft7Validator.check_schema(endpoint["schema"])
            except Exception as error:
                raise RuntimeError("ValidationError: %s" % str(error))
            return fn(endpoint, **kwargs)
        return wrapped
    def add_schema_metadata(fn):
        def wrapped(endpoint, **kwargs):
            endpoint["schema"]["$schema"]=Draft7Schema
            return fn(endpoint, **kwargs)
        return wrapped
    @validate_schema
    @add_schema_metadata
    @resource(suffix=suffix)
    def ApiModel(endpoint, **kwargs):
        root=ref("%s-root" % kwargs["name"])
        name=logical_id("%s-%s-model" % (kwargs["name"],
                                         endpoint["name"]))
        props={"RestApiId": root,
               "ContentType": "application/json",
               "Name": name,
               "Schema": endpoint["schema"]}
        return "AWS::ApiGateway::Model", props
    return ApiModel(endpoint, **kwargs)

"""
- creation/deletion of AWS::ApiGateway::Method can be a pain
- often newly registered dependent resource only appear on second deployment
- and deletion can fail due to dependency ordering
- advice is to use depends liberally :-)
- https://console.aws.amazon.com/support/home#/case/?displayId=7271579711&language=en
"""

def ApiMethod(endpoint, **kwargs):
    def root_name(kwargs):
        return "%s-root" % kwargs["name"]
    def resource_name(endpoint, kwargs):
        return "%s-%s-resource" % (kwargs["name"],
                                   endpoint["name"])
    def validator_name(endpoint, kwargs):
        return "%s-%s-validator" % (kwargs["name"],
                                    endpoint["name"])
    def model_name(endpoint, kwargs):
        return "%s-%s-model" % (kwargs["name"],
                                endpoint["name"])
    suffix="%s-method" % endpoint["name"]
    @resource(suffix=suffix)
    def ApiMethod(endpoint, **kwargs):
        target=ref("%s-arn" % endpoint["action"])
        uri=fn_sub(LambdaInvokeArn % kwargs["region"],
                   {"lambda_arn": target})
        integration={"Uri": uri,
                     "IntegrationHttpMethod": "POST",
                     "Type": "AWS_PROXY"}
        root=root_name(kwargs)
        parent=resource_name(endpoint, kwargs)
        props={"AuthorizationType": "NONE",
               "RestApiId": ref(root),
               "ResourceId": ref(parent),
               "HttpMethod": endpoint["method"],
               "Integration": integration}
        depends=[root, parent]
        if ("params" in endpoint or
            "schema" in endpoint):
            validator=validator_name(endpoint, kwargs)
            props["RequestValidatorId"]=ref(validator)
            depends.append(validator)
        if "params" in endpoint:
            params={"method.request.querystring.%s" % param:True
                    for param in endpoint["params"]}
            props["RequestParameters"]=params
        if "schema" in endpoint:
            model=model_name(endpoint, kwargs)
            models={"application/json": logical_id(model)}
            props["RequestModels"]=models
            depends.append(model)
        return "AWS::ApiGateway::Method", props, depends
    return ApiMethod(endpoint, **kwargs)

def ApiCorsOptions(endpoint, **kwargs):
    suffix="%s-cors-options" % endpoint["name"]
    @resource(suffix=suffix)
    def ApiCorsOptions(endpoint, **kwargs):
        def init_integration_response(endpoint):
            params={CorsHeaderPath % k.capitalize(): "'%s'" % v # NB "'"
                    for k, v in [("headers", ",".join(CorsHeaders)),
                                 ("methods", "%s,OPTIONS" % endpoint["method"]),
                                 ("origin", "*")]}
            templates={"application/json": ""}
            return {"StatusCode": 200,
                    "ResponseParameters": params,
                    "ResponseTemplates": templates}
        def init_integration(endpoint):
            templates={"application/json": json.dumps({"statusCode": 200})}
            response=init_integration_response(endpoint)
            return {"IntegrationResponses": [response],
                    "PassthroughBehavior": "WHEN_NO_MATCH",
                    "RequestTemplates": templates,
                    "Type": "MOCK"}
        def init_response():
            params={CorsHeaderPath % k.capitalize(): False
                    for k in ["headers", "methods", "origin"]}
            models={"application/json": "Empty"}
            return {"StatusCode": 200,
                    "ResponseModels": models,
                    "ResponseParameters": params}
        root=ref("%s-root" % kwargs["name"])
        parent=ref("%s-%s-resource" % (kwargs["name"],
                                       endpoint["name"]))
        integration=init_integration(endpoint)
        response=init_response()
        props={"AuthorizationType": "NONE",
               "HttpMethod": "OPTIONS",
               "Integration": integration,
               "MethodResponses": [response],
               "ResourceId": parent,
               "RestApiId": root}
        return "AWS::ApiGateway::Method", props
    return ApiCorsOptions(endpoint, **kwargs)

def ActionPermission(endpoint, **kwargs):
    suffix="%s-permission" % endpoint["name"]
    @resource(suffix=suffix)
    def ActionPermission(endpoint, **kwargs):
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
    return ActionPermission(endpoint, **kwargs)

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

def synth_api(template, **kwargs):
    template.update(Resources=[ApiRoot(**kwargs),
                               ApiAccount(**kwargs),
                               ApiLogsRole(**kwargs),
                               ApiDeployment(**kwargs),
                               ApiStage(**kwargs)])
    for endpoint in kwargs["resources"]:
        template.update(Parameters=parameter("%s-arn" % endpoint["action"]),
                        Resources=[ApiResource(endpoint, **kwargs),
                                   ApiMethod(endpoint, **kwargs),
                                   ApiCorsOptions(endpoint, **kwargs),
                                   ActionPermission(endpoint, **kwargs)],
                        Outputs=ApiUrl(endpoint, **kwargs))
        if ("params" in endpoint or
            "schema" in endpoint):
            template.update(Resources=ApiValidator(endpoint, **kwargs))
        if "schema" in endpoint:
            template.update(Resources=ApiModel(endpoint, **kwargs))
                            
if __name__=="__main__":
    pass
