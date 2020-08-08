from pareto.components import *

"""
- s3 ARNs contain neither region nor account id
"""

Arn="arn:aws:s3:::%s"

@resource()
def Bucket(event={"type":  "s3:ObjectCreated:*"},
           **kwargs):
    def lambda_config(kwargs, event):
        target=ref("%s-arn" % kwargs["action"])
        return {"Event": event["type"],
                "Function": target}
    props={"BucketName": resource_name(kwargs)}
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

def synth_bucket(**kwargs):
    template=Template(Resources=Bucket(**kwargs))
    if "action" in kwargs:
        template.update(Parameters=parameter("%s-arn" % kwargs["action"]),
                        Resources=BucketPermission(**kwargs))
    return template

if __name__=="__main__":
    pass
