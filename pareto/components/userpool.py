from pareto.components import *

from pareto.components.role import IAMRole, DefaultRolePolicyDoc

CognitoUserPoolArn="arn:aws:cognito-idp:${AWS::Region}:${AWS::AccountId}:userpool/${user_pool}"

ParamNames=yaml.safe_load("""
- app-name
- stage-name
- runtime-version
""")

UserAttrs=["email"]

AdminSignUpEmailLambda="""def handler(event, context):
if event["triggerSource"]=="CustomMessage_AdminCreateUser":
  event["response"]["emailSubject"]="Welcome to {service}!"
  event["response"]["emailMessage"]="Your username is "+event["request"]["usernameParameter"]+" and your temporary password is "+event["request"]["codeParameter"]
return event
"""

DefaultPermissions=yaml.safe_load("""
- logs:CreateLogGroup
- logs:CreateLogStream
- logs:PutLogEvents                                          
""")

@resource(suffix="user-pool")
def UserPool(userattrs=UserAttrs,
             minpasswordlength=8,
             **kwargs):
    policies={"PasswordPolicy": {"MinimumLength": minpasswordlength}}
    schema=[{"AttributeDataType": "String",
             "Name": attr,
             "Required": True}
            for attr in userattrs]
    props={"Policies": policies,
           "AutoVerifiedAttributes": userattrs,
           "UsernameAttributes": userattrs,
           "Schema": schema}
    return "AWS::Cognito::UserPool", props

@resource(suffix="user-pool-admin-signup-function")
def UserPoolAdminSignupFunction(handler="index.handler",
                                memory=128,
                                timeout=30,
                                **kwargs):
    rolearn=fn_getatt("%s-user-pool-admin-signup-role" % kwargs["name"], "Arn")
    code=AdminSignUpEmailLambda.format(service=kwargs["email"]["service_name"])
    props={"Code": {"ZipFile": code},
           "Handler": handler,
           "MemorySize": memory,
           "Role": rolearn,           
           "Runtime": fn_sub("python${version}",
                             {"version": ref("runtime-version")}),
           "Timeout": timeout}
    return "AWS::Lambda::Function", props

@resource(suffix="user-pool-admin-signup-role")
def UserPoolAdminSignupRole(**kwargs):
    def role_policy_doc():
        return DefaultRolePolicyDoc("lambda.amazonaws.com")
    return IAMRole(rolepolicyfn=role_policy_doc,
                   defaults=DefaultPermissions,
                   **kwargs)

@resource(suffix="user-pool-admin-signup-permission")
def UserPoolAdminSignupPermission(**kwargs):
    source=fn_sub(CognitoUserPoolArn,
                  {"user_pool": ref("%s-user-pool" % kwargs["name"])})
    target=ref("%s-user-pool-admin-signup-function" % kwargs["name"])
    props={"Action": "lambda:InvokeFunction",
           "FunctionName": target,
           "Principal": "cognito-idp.amazonaws.com",
           "SourceArn": source}
    return "AWS::Lambda::Permission", props

@resource(suffix="user-pool-web-client")
def UserPoolWebClient(userattrs=UserAttrs,
                      authflows=["ALLOW_USER_SRP_AUTH",
                                 "ALLOW_REFRESH_TOKEN_AUTH"],
                      **kwargs):
    userpool=ref("%s-user-pool" % kwargs["name"])
    props={"UserPoolId": userpool,
           "PreventUserExistenceErrors": "ENABLED",
           "ExplicitAuthFlows": authflows}
    return "AWS::Cognito::UserPoolClient", props

@resource(suffix="user-pool-admin-client")
def UserPoolAdminClient(userattrs=UserAttrs,
                        authflows=["ALLOW_ADMIN_USER_PASSWORD_AUTH",
                                   "ALLOW_REFRESH_TOKEN_AUTH"],
                        **kwargs):
    userpool=ref("%s-user-pool" % kwargs["name"])
    props={"UserPoolId": userpool,
           "PreventUserExistenceErrors": "ENABLED",
           "ExplicitAuthFlows": authflows}
    return "AWS::Cognito::UserPoolClient", props

@output(suffix="user-pool-id")
def UserPoolId(**kwargs):
    return ref("%s-user-pool" % kwargs["name"])

"""
- APIGW authorizer requires user pool ARN
"""

@output(suffix="user-pool-arn")
def UserPoolArn(**kwargs):
    return fn_getatt("%s-user-pool" % kwargs["name"], "Arn")

@output(suffix="user-pool-web-client-id")
def UserPoolWebClientId(**kwargs):
    return ref("%s-user-pool-web-client" % kwargs["name"])

@output(suffix="user-pool-admin-client-id")
def UserPoolAdminClientId(**kwargs):
    return ref("%s-user-pool-admin-client" % kwargs["name"])

def synth_userpool(template, **kwargs):
    template.update(Parameters=[parameter(paramname)
                                for paramname in ParamNames],
                    Resources=[UserPool(**kwargs),
                               UserPoolAdminSignupFunction(**kwargs),
                               UserPoolAdminSignupRole(**kwargs),
                               UserPoolAdminSignupPermission(**kwargs),
                               UserPoolWebClient(**kwargs),
                               UserPoolAdminClient(**kwargs)],
                    Outputs=[UserPoolId(**kwargs),
                             UserPoolArn(**kwargs),
                             UserPoolWebClientId(**kwargs),
                             UserPoolAdminClientId(**kwargs)])

if __name__=="__main__":
    pass
