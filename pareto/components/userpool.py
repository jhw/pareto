from pareto.components import *

from pareto.components.role import IAMRole

# https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-cognito-userpoolclient.html#cfn-cognito-userpoolclient-explicitauthflows

"""
- seems ALLOW_ADMIN_USER_PASSWORD_AUTH is required for boto3 admin login
- but specifying that alone causes Cognito create failure
- so specify all except *_USER_PASSWORD_* which feels insecure
- default flows (ExplicitAuthFlows not set) work with JS
"""

ExplicitAuthFlows=yaml.safe_load("""
- ALLOW_ADMIN_USER_PASSWORD_AUTH
# - ADMIN_USER_PASSWORD_AUTH
- ALLOW_CUSTOM_AUTH
# - ALLOW_USER_PASSWORD_AUTH
- ALLOW_USER_SRP_AUTH
- ALLOW_REFRESH_TOKEN_AUTH
""")

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

@resource(suffix="user-pool-client")
def UserPoolClient(userattrs=UserAttrs,
                   authflows=ExplicitAuthFlows,
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

@output(suffix="user-pool-client-id")
def UserPoolClientId(**kwargs):
    return ref("%s-user-pool-client" % kwargs["name"])

def synth_userpool(template, **kwargs):
    template.update(Parameters=[parameter(paramname)
                                for paramname in ParamNames],
                    Resources=[UserPool(**kwargs),
                               UserPoolClient(**kwargs)],
                    Outputs=[UserPoolId(**kwargs),
                             UserPoolArn(**kwargs),
                             UserPoolClientId(**kwargs)])

if __name__=="__main__":
    pass
