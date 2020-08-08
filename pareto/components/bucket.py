from pareto.components import *

"""
- s3 ARNs contain neither region nor account id
"""

Arn="arn:aws:s3:::%s"

@resource()
def Bucket(event={"type":  "s3:ObjectCreated:*"},
           **kwargs):
    def website_config(index="index.json"):
        corsrules=[{"AllowedMethods": ["GET"],
                    "AllowedOrigins": ["*"]}]
        corsconfig={"CorsRules": corsrules}
        websiteconfig={"IndexDocument": index}
        return {"AccessControl": "PublicRead",
                "CorsConfiguration": corsconfig,
                "WebsiteConfiguration": websiteconfig}
    def lambda_config(kwargs, event):
        target=ref("%s-arn" % kwargs["action"])
        return {"Event": event["type"],
                "Function": target}
    props={"BucketName": resource_name(kwargs)}
    if "website" in kwargs and kwargs["website"]:
        props.update(website_config())
    if "action" in kwargs:
        notifications={"LambdaConfigurations": [lambda_config(kwargs, event)]}
        props["NotificationConfiguration"]=notifications
    return "AWS::S3::Bucket", props

@resource(suffix="permission")
def BucketPermission(**kwargs):
    source=Arn % resource_name(kwargs)
    target=ref("%s-arn" % kwargs["action"])
    props={"Action": "lambda:InvokeFunction",
           "FunctionName": target,
           "SourceAccount": fn_sub("${AWS::AccountId}"), # recommended as arn does not contain account
           "SourceArn": source,
           "Principal": "s3.amazonaws.com"}
    return "AWS::Lambda::Permission", props

@output(suffix="website-url")
def BucketWebsiteUrl(**kwargs):
    return fn_getatt(kwargs["name"], "WebsiteURL")

@resource(suffix="website-policy")
def BucketWebsitePolicy(**kwargs):
    def policy_document(kwargs):
        resource=fn_sub(Arn, {"bucket_name": ref(kwargs["name"])})
        statement=[{"Action": "s3:GetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Resource": resource}]
        return {"Statement": statement,
                "Version": "2012-10-17"}
    props={"Bucket": ref(kwargs["name"]),
           "PolicyDocument": policy_document(kwargs)}
    return "AWS::S3::BucketPolicy", props

def synth_bucket(**kwargs):
    template=Template(Resources=Bucket(**kwargs))
    if "action" in kwargs:
        template.update(Parameters=parameter("%s-arn" % kwargs["action"]),
                        Resources=BucketPermission(**kwargs))
    if "website" in kwargs and kwargs["website"]:
        template.update(Resources=BucketWebsitePolicy(**kwargs),
                        Outputs=BucketWebsiteUrl(**kwargs))
    return template

if __name__=="__main__":
    pass
