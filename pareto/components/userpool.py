from pareto.components import *

from pareto.components.role import IAMRole

ParamNames=yaml.safe_load("""
- app-name
- stage-name
""")

UserAttrs=["email"]

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
                               UserPoolWebClient(**kwargs),
                               UserPoolAdminClient(**kwargs)],
                    Outputs=[UserPoolId(**kwargs),
                             UserPoolArn(**kwargs),
                             UserPoolWebClientId(**kwargs),
                             UserPoolAdminClientId(**kwargs)])

if __name__=="__main__":
    pass
