from pareto.components import *

@resource()
def Bucket(event={"type":  "s3:ObjectCreated:*"},
           **kwargs):
    def lambda_config(kwargs, event):
        funcarn=ref("%s-arn" % kwargs["action"])
        return {"Event": event["type"],
                "Function": funcarn}
    props={"BucketName": resource_name(kwargs)}
    if "action" in kwargs:
        notifications={"LambdaConfigurations": [lambda_config(kwargs, event)]}
        props["NotificationConfiguration"]=notifications
    return "AWS::S3::Bucket", props

@resource(suffix="permission")
def BucketPermission(**kwargs):
    """
        - https://aws.amazon.com/premiumsupport/knowledge-center/unable-validate-circular-dependency-cloudformation/
        - Fn::GetAtt Arn doesn't work for S3 lambda notifications :-(
        - NB also recommends using SourceAccount as account not included in S3 arn format
        """
    source="arn:aws:s3:::%s" % resource_name(kwargs)
    funcarn=ref("%s-arn" % kwargs["action"])
    props={"Action": "lambda:InvokeFunction",
           "FunctionName": funcarn,
           "SourceAccount": fn_sub("${AWS::AccountId}"),
           "SourceArn": source,
           "Principal": "s3.amazonaws.com"}
    return "AWS::Lambda::Permission", props

def synth_bucket(**kwargs):
    template=Template(resources=[Bucket(**kwargs)])
    if "action" in kwargs:
        template.parameters.append(parameter("%s-arn" % kwargs["action"]))
        template.resources.append(BucketPermission(**kwargs))
    return template

if __name__=="__main__":
    pass
