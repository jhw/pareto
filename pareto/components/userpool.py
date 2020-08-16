from pareto.components import *

CallbackUrl="https://%s.auth.${AWS::Region}.amazoncognito.com/callback"

LogoutUrl="https://%s.auth.${AWS::Region}.amazoncognito.com"

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
    callbackurl=CallbackUrl % resource_name(kwargs)
    logouturl=LogoutUrl % resource_name(kwargs)
    props={"UserPoolId": userpool,
           "GenerateSecret": False,
           "PreventUserExistenceErrors": "ENABLED",
           "SupportedIdentityProviders": ["COGNITO"],
           "CallbackURLs": [callbackurl],
           "LogoutURLs": [logouturl],
           "ExplicitAuthFlows": authflows,
           "AllowedOAuthFlowsUserPoolClient": True,
           "AllowedOAuthFlows": ["code"],
           "AllowedOAuthScopes": UserAttrs+["openid",
                                            "profile"]}
    return "AWS::Cognito::UserPoolClient", props

@resource(suffix="identity-pool")
def IdentityPool(**kwargs):
    client=ref("%s-user-pool-client" % kwargs["name"])
    providername=fn_getatt("%s-user-pool" % kwargs["name"],
                           "ProviderName")
    provider={"ClientId": client,
              "ProviderName": providername}
    props={"CognitoIdentityProviders": [provider],
           "AllowUnauthenticatedIdentities": False}
    return "AWS::Cognito::IdentityPool", props

@resource(suffix="roles")
def IdentityPoolRoles(**kwargs):
    identitypool=ref("%s-identity-pool" % kwargs["name"])
    authrole=fn_getatt("%s-auth-role" % kwargs["name"], "Arn")
    roles={"authenticated": authrole}
    props={"IdentityPoolId": identitypool,
           "Roles": roles}
    return "AWS::Cognito::IdentityPoolRoleAttachment", props

def IdentityPoolRole(name, authtype, permissions):
    def assume_role_policy_doc(name, authtype):
        identitypool=ref("%s-identity-pool" % name)
        condition={"StringEquals": {"cognito-identity.amazonaws.com:aud": identitypool},
                   "ForAnyValue:StringLike": {"cognito-identity.amazonaws.com:amr": authtype}}
        principal={"Federated": "cognito-identity.amazonaws.com"}
        statement=[{"Action": "sts:AssumeRoleWithWebIdentity",
                    "Effect": "Allow",
                    "Condition": condition,
                    "Principal": principal}]
        return {"Statement": statement,
                "Version": "2012-10-17"}
    def policy(permissions):
        statement=[{"Action": permission,
                    "Effect": "Allow",
                    "Resource": "*"}
                   for permission in permissions]
        return {"PolicyDocument": {"Statement": statement,
                                   "Version": "2012-10-17"},
                "PolicyName": random_id("inline-policy")}
    props={"AssumeRolePolicyDocument": assume_role_policy_doc(name,
                                                              authtype)}
    props["Policies"]=[policy(permissions)]
    return "AWS::IAM::Role", props
    
@resource(suffix="auth-role")
def IdentityPoolAuthRole(**kwargs):
    return IdentityPoolRole(name=kwargs["name"],
                            authtype="authenticated",
                            permissions=["mobileanalytics:PutEvents",
                                         "cognito-sync:*",
                                         "cognito-identity:*",
                                         "lambda:InvokeFunction"])

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

@output(suffix="identity-pool-id")
def IdentityPoolId(**kwargs):
    return ref("%s-identity-pool" % kwargs["name"])

def synth_userpool(template, **kwargs):
    template.update(Resources=[UserPool(**kwargs),
                               UserPoolClient(**kwargs),
                               IdentityPool(**kwargs),
                               IdentityPoolRoles(**kwargs),
                               IdentityPoolAuthRole(**kwargs)],
                    Outputs=[UserPoolId(**kwargs),
                             UserPoolArn(**kwargs),
                             UserPoolClientId(**kwargs),
                             IdentityPoolId(**kwargs)])

if __name__=="__main__":
    from pareto.template import Template
    template=Template()
    kwargs={"app": "pareto-demo",
            "name": "hello-pool",
            "stage": "dev"}
    synth_userpool(template, **kwargs)
    print (template.yaml_repr)


