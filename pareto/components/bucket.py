from pareto.components import *

PermissionArn="arn:aws:s3:::${resource_name}"

WebsitePolicyArn="arn:aws:s3:::${bucket_name}/*"

ParamNames=yaml.safe_load("""
- app-name
- stage-name
""")

@resource()
def Bucket(**kwargs):
    def website_config(index="index.json"):
        corsrules=[{"AllowedMethods": ["GET"],
                    "AllowedOrigins": ["*"]}]
        corsconfig={"CorsRules": corsrules}
        websiteconfig={"IndexDocument": index}
        return {"AccessControl": "PublicRead",
                "CorsConfiguration": corsconfig,
                "WebsiteConfiguration": websiteconfig}
    def lambda_config(action):
        target=ref("%s-arn" % action["name"])
        rules=[{"Name": "prefix",
                "Value": action["path"]}]
        return {"Event": "s3:ObjectCreated:*",
                "Function": target,
                "Filter": {"S3Key": {"Rules": rules}}}
    props={"BucketName": resource_name(kwargs)}
    if "website" in kwargs and kwargs["website"]:
        props.update(website_config())
    if "actions" in kwargs:
        lambdaconfig=[lambda_config(action)
                      for action in kwargs["actions"]]
        notifications={"LambdaConfigurations": lambdaconfig}
        props["NotificationConfiguration"]=notifications
    return "AWS::S3::Bucket", props

def ActionPermission(action, **kwargs):
    suffix="%s-permission" % action["name"]
    @resource(suffix=suffix)
    def ActionPermission(action, **kwargs):
        source=fn_sub(PermissionArn,
                      {"resource_name": resource_name(kwargs)})
        target=ref("%s-arn" % action["name"])
        props={"Action": "lambda:InvokeFunction",
               "FunctionName": target,
               "SourceAccount": fn_sub("${AWS::AccountId}"), # recommended as arn does not contain account
               "SourceArn": source,
               "Principal": "s3.amazonaws.com"}
        return "AWS::Lambda::Permission", props
    return ActionPermission(action, **kwargs)

@output(suffix="website-url")
def BucketWebsiteUrl(**kwargs):
    return fn_getatt(kwargs["name"], "WebsiteURL")

@resource(suffix="website-policy")
def BucketWebsitePolicy(**kwargs):
    def policy_document(kwargs):
        resource=fn_sub(WebsitePolicyArn,
                        {"bucket_name": ref(kwargs["name"])})
        statement=[{"Action": "s3:GetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Resource": resource}]
        return {"Statement": statement,
                "Version": "2012-10-17"}
    props={"Bucket": ref(kwargs["name"]),
           "PolicyDocument": policy_document(kwargs)}
    return "AWS::S3::BucketPolicy", props

def synth_bucket(template, **kwargs):
    template.update(Parameters=[parameter(paramname)
                                for paramname in ParamNames],
                    Resources=Bucket(**kwargs))
    if "actions" in kwargs:
        for action in kwargs["actions"]:
            template.update(Parameters=parameter("%s-arn" % action["name"]),
                            Resources=ActionPermission(action, **kwargs))
    if "website" in kwargs and kwargs["website"]:
        template.update(Resources=BucketWebsitePolicy(**kwargs),
                        Outputs=BucketWebsiteUrl(**kwargs))

if __name__=="__main__":
    pass
