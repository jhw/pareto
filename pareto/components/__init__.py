import json, re, yaml

def resource_id(kwargs):
    def labelise(text):
        return "-".join([tok.lower()
                         for tok in re.split("\\s|\\_", text)])    
    return "-".join([labelise(kwargs[attr])
                     for attr in ["app", "name", "stage"]])

def logical_id(name):
    def hungarorise(text):
        return "".join([tok.capitalize()
                        for tok in re.split("\\-|\\_", text)])    
    return hungarorise(name)

def ref(name):
    return {"Ref": logical_id(name)}

def fn_getatt(name, attr):
    return {"Fn::GetAtt": [logical_id(name), attr]}

def fn_join(args, delimiter=""):    
    return {"Fn::Join": [delimiter, args]}

def fn_sub(expr, kwargs={}):    
    return {"Fn::Sub": [expr, kwargs]}

def parameter(name, type_="String"):
    return (logical_id(name), {"Type": type_})

def resource(suffix=None):
    def format_depends(v):
        return [logical_id(name)
                for name in v]
    def format_value(k, v):
        return format_depends(v) if k=="DependsOn" else v
    def decorator(fn):
        def wrapped(attrs=["Type", "Properties", "DependsOn"],
                    *args, **kwargs):
            name="%s-%s" % (kwargs["name"],
                            suffix) if suffix else kwargs["name"]
            key=logical_id(name)
            values=fn(*args, **kwargs)
            return (key, {k:format_value(k, v)
                          for k, v in zip(attrs[:len(values)],
                                          values)})
        return wrapped
    return decorator

def output(suffix=None):
    def decorator(fn):
        def wrapped(*args, **kwargs):
            name="%s-%s" % (kwargs["name"],
                            suffix) if suffix else kwargs["name"]
            return (logical_id(name),
                    {"Value": fn(*args, **kwargs)})
        return wrapped
    return decorator

class Template(dict):

    def __init__(self, **kwargs):
        dict.__init__(self, kwargs)
        for attr in ["parameters",
                     "resources",
                     "outputs"]:
            self.setdefault(attr, [])

    def trim(self):
        return {k:v for k, v in self.items()
                if v!=[]}

@resource(suffix="role")
def IamRole(**kwargs):
    def assume_role_policy_doc():
        statement=[{"Action": "sts:AssumeRole",
                    "Effect": "Allow",
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
    if "policies" in kwargs:
        props["ManagedPolicyArns"]=kwargs["policies"]
    return "AWS::IAM::Role", props

if __name__=="__main__":
    pass
