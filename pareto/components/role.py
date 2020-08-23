from pareto.components import *

def IAMRole(service,
            defaults=[],
            **kwargs):
    def role_policy_doc(service):
        statement=[{"Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Principal": {"Service": service}}]
        return {"Statement": statement,
                "Version": "2012-10-17"}    
    def default_permissions(fn):
        def wrapped(kwargs):
            permissions=set(kwargs["permissions"]) if "permissions" in kwargs else set()
            permissions.update(defaults)
            return fn(list(permissions))
        return wrapped
    def assert_permissions(fn):
        def wrapped(permissions):
            wildcards=[permission
                       for permission in permissions
                       if permission.endswith(":*")]
            if wildcards!=[]:
                raise RuntimeError("IAM wildcards detected - %s" % ", ".join(wildcards))
            return fn(permissions)
        return wrapped
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
    @default_permissions
    # @assert_permissions
    @group_permissions
    def policy(groups):
        statement=[{"Action": permissions,
                    "Effect": "Allow",
                    "Resource": "*"}
                   for permissions in groups]
        return {"PolicyDocument": {"Statement": statement,
                                   "Version": "2012-10-17"},
                "PolicyName": random_id("inline-policy")}
    props={"AssumeRolePolicyDocument": role_policy_doc(service)}
    props["Policies"]=[policy(kwargs)]
    return "AWS::IAM::Role", props
