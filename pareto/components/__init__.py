import json, re, yaml

def hungarorise(text):
    return "".join([tok.capitalize()
                    for tok in re.split("\\-|\\_", text)])

def titleise(text):
    return " ".join([tok.capitalize()
                     for tok in re.split("\\-|\\_", text)])

def labelise(text):
    return "-".join([tok.lower()
                    for tok in re.split("\\s|\\_", text)])

def ref(name):
    return {"Ref": hungarorise(name)}

def fn_getatt(name, attr):
    return {"Fn::GetAtt": [hungarorise(name), attr]}

def fn_join(args, delimiter=""):    
    return {"Fn::Join": [delimiter, args]}

def fn_sub(expr, kwargs={}):    
    return {"Fn::Sub": [expr, kwargs]}

def global_name(kwargs):
    return "-".join([labelise(kwargs[attr])
                     for attr in ["app", "name", "stage"]])

def parameter(suffix=None):
    def decorator(fn):
        def wrapped(*args, **kwargs):
            name="%s-%s" % (kwargs["name"],
                            suffix) if suffix else kwargs["name"]
            return (hungarorise(name),
                    fn(*args, **kwargs))
        return wrapped
    return decorator

def resource(suffix=None):
    def decorator(fn):
        def wrapped(*args, **kwargs):
            name="%s-%s" % (kwargs["name"],
                            suffix) if suffix else kwargs["name"]
            key=hungarorise(name)
            attrs=["Type", "Properties"]
            values=fn(*args, **kwargs)
            if len(values) > 2:
                attrs.append("DependsOn")
            return (key, {k:v for k, v in zip(attrs, values)})
        return wrapped
    return decorator

def output(suffix=None):
    def decorator(fn):
        def wrapped(*args, **kwargs):
            name="%s-%s" % (kwargs["name"],
                            suffix) if suffix else kwargs["name"]
            return (hungarorise(name),
                    {"Value": fn(*args, **kwargs)})
        return wrapped
    return decorator

@parameter()
def Parameter(type="String",
              value=None,
              **kwargs):
    param={"Type": type}
    if value:
        param["DefaultValue"]=value
    return param

@resource(suffix="role")
def IamRole(**kwargs):
    def assume_role_policy_doc():
        statement=[{"Action": "sts:AssumeRole",
                    "Effect": "allow",
                    "Principal": {"Service": kwargs["service"]}}]
        return {"Statement": statement,
                "Version": "2012-10-17"}
    def policy(permissions):
        """
        policy name required I believe
        """
        name="%s-policy" % kwargs["name"]
        statement=[{"Action": permission,
                    "Effect": "Allow",
                    "Resource": "*"}
                   for permission in permissions]
        return {"PolicyDocument": {"Statement": statement,
                                   "Version": "2012-10-17"},
                "PolicyName": name}
    props={"AssumeRolePolicyDocument": assume_role_policy_doc()}
    if "permissions" in kwargs:
        """
        single policy only for the moment
        """
        props["Policies"]=[policy(kwargs["permissions"])]
    if "managed_policies" in kwargs:
        props["ManagedPolicyArns"]=kwargs["managed_policies"]
    return "AWS::IAM::Role", props

if __name__=="__main__":
    pass
