from pareto.components import *

from pareto.components.bucket import BucketPermission

"""
- s3 arns contain neither region nor account id
"""

Arn="arn:aws:s3:::${bucket_name}/*"

@resource()
def Website(event={"type":  "s3:ObjectCreated:*"},
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
    props.update(website_config())
    if "action" in kwargs:
        notifications={"LambdaConfigurations": [lambda_config(kwargs, event)]}
        props["NotificationConfiguration"]=notifications
    return "AWS::S3::Bucket", props

@output(suffix="url")
def WebsiteUrl(**kwargs):
    return fn_getatt(kwargs["name"], "WebsiteURL")

@resource(suffix="policy")
def WebsitePolicy(**kwargs):
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

def synth_website(**kwargs):
    template=Template({"Parameters": {},
                       "Resources": dict([Website(**kwargs),
                                          WebsitePolicy(**kwargs)]),
                       "Outputs": dict([WebsiteUrl(**kwargs)])})
    if "action" in kwargs:
        template["Parameters"].update(dict([parameter("%s-arn" % kwargs["name"])]))
        template["Resources"].update(dict([BucketPermission(**kwargs)]))
    return template

if __name__=="__main__":
    pass
