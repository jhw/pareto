from pareto.components import *

def DefaultRolePolicyDoc(service):
    statement=[{"Action": "sts:AssumeRole",
                "Effect": "Allow",
                "Principal": {"Service": service}}]
    return {"Statement": statement,
            "Version": "2012-10-17"}

def IAMRole(rolepolicyfn,        
            defaults=[],
            wildcards=False,
            **kwargs):
    def default_permissions(defaults):
        def decorator(fn):
            def wrapped(kwargs):
                permissions=set(kwargs["permissions"]) if "permissions" in kwargs else set()
                permissions.update(defaults)
                return fn(list(permissions))
            return wrapped
        return decorator
    def assert_permissions(allow):
        def decorator(fn):
            def wrapped(permissions):
                if not allow:
                    wildcards=[permission
                               for permission in permissions
                               if permission.endswith(":*")]
                    if wildcards!=[]:
                        raise RuntimeError("IAM wildcards detected - %s" % ", ".join(wildcards))
                return fn(permissions)
            return wrapped
        return decorator
    def group_permissions(fn):
        def wrapped(permissions):
            groups={}
            for permission in permissions:
                key=permission.split(":")[0]
                groups.setdefault(key, [])
                groups[key].append(permission)
            return fn([sorted(group)
                       for group in groups.values()])
        return wrapped
    @default_permissions(defaults)
    @assert_permissions(wildcards)
    @group_permissions
    def policy(groups):
        statement=[{"Action": permissions,
                    "Effect": "Allow",
                    "Resource": "*"}
                   for permissions in groups]
        return {"PolicyDocument": {"Statement": statement,
                                   "Version": "2012-10-17"},
                "PolicyName": random_id("inline-policy")}
    props={"AssumeRolePolicyDocument": rolepolicyfn()}
    props["Policies"]=[policy(kwargs)]
    return "AWS::IAM::Role", props
