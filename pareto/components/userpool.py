@resource(suffix="user-pool")
def UserPool(**kwargs):
    props={}
    return "AWS::Cognito::UserPool", props

@resource(suffix="user-pool-client")
def UserPoolClient(**kwargs):
    props={}
    return "AWS::Cognito::UserPoolClient", props

@resource(suffix="identity-pool")
def IdentityPool(**kwargs):
    props={}
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

def synth_userpool(template, **kwargs):
    template.update(Resources=[UserPool(**kwargs),
                               UserPoolClient(**kwargs),
                               IdentityPool(**kwargs),
                               IdentityPoolRoles(**kwargs),
                               IdentityPoolAuthRole(**kwargs),
                               IdentityPoolUnauthRole(**kwargs)])

if __name__=="__main__":
    pass

