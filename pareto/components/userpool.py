from pareto.components import *

CallbackUrl="https://apigw-auth-demo.auth.${AWS::Region}.amazoncognito.com/callback"

LogoutUrl="https://apigw-auth-demo.auth.${AWS::Region}.amazoncognito.com"

UserAttrs=["email"]

@resource(suffix="user-pool")
def UserPool(userattrs=UserAttrs,
             minpasswordlength=8,
             **kwargs):
    policies={"PasswordPolicy": {"MinimumLength": minpasswordlength}}
    schema=[{"AttributeDataType": "string",
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
                   **kwargs):
    userpool=ref("%s-user-pool" % kwargs["name"])
    props={"UserPoolId": userpool,
           "GenerateSecret": False,
           "PreventUserExistenceErrors": "ENABLED",
           "SupportedIdentityProviders": ["COGNITO"],
           "CallbackURLs": [CallbackUrl],
           "LogoutURLs": [LogoutUrl],
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
           "AllowUnauthenticatedIdentities": True}
    return "AWS::Cognito::IdentityPool", props

@resource(suffix="identity-pool-roles")
def IdentityPoolRoles(**kwargs):
    props={}
    return "AWS::Cognito::IdentityPoolRoleAttachment", props

@resource(suffix="identity-pool-auth-role")
def IdentityPoolAuthRole(**kwargs):
    props={}
    return "AWS::IAM::Role", props

@resource(suffix="identity-pool-unauth-role")
def IdentityPoolUnauthRole(**kwargs):
    props={}
    return "AWS::IAM::Role", props

@output(suffix="user-pool-id")
def UserPoolId(**kwargs):
    return ref("%s-user-pool" % kwargs["name"])

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
                               IdentityPoolAuthRole(**kwargs),
                               IdentityPoolUnauthRole(**kwargs)],
                    Outputs=[UserPoolId(**kwargs),
                             UserPoolClientId(**kwargs),
                             IdentityPoolId(**kwargs)])

if __name__=="__main__":
    from pareto.template import Template
    template=Template()
    kwargs={"name": "hello-pool"}
    synth_userpool(template, **kwargs)
    print (template.yaml_repr)


