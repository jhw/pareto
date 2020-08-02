from pareto.components import *

@resource()
def Bucket(event={"type":  "s3:ObjectCreated:*"},
           **kwargs):
    def lambda_config(kwargs, event):
        funcarn=fn_getatt("%s-action" % kwargs["name"], "Arn")
        return {"Event": event["type"],
                "Function": funcarn}
    props={"BucketName": resource_name(kwargs)}
    if "action" in kwargs:
        notifications={"LambdaConfigurations": [lambda_config(kwargs, event)]}
        props["NotificationConfiguration"]=notifications
    return "AWS::S3::Bucket", props

@resource(suffix="action-permission")
def BucketActionPermission(**kwargs):
    """
        - https://aws.amazon.com/premiumsupport/knowledge-center/unable-validate-circular-dependency-cloudformation/
        - Fn::GetAtt Arn doesn't work for S3 lambda notifications :-(
        - NB also recommends using SourceAccount as account not included in S3 arn format
        """
    eventsource="arn:aws:s3:::%s" % resource_name(kwargs)
    funcarn=fn_getatt("%s-action" % kwargs["name"], "Arn")
    props={"Action": "lambda:InvokeFunction",
           "FunctionName": funcarn,
           "SourceAccount": fn_sub("${AWS::AccountId}"),
           "SourceArn": eventsource,
           "Principal": "s3.amazonaws.com"}
    return "AWS::Lambda::Permission", props

@output(suffix="arn")
def BucketArn(**kwargs):
    return fn_getatt(kwargs["name"], "Arn")

def synth_bucket(**kwargs):
    template=Template(resources=[Bucket(**kwargs)],
                      outputs=[BucketArn(**kwargs)])
    if "action" in kwargs:
        template.resources.append(BucketActionPermission(**kwargs))
    return template

if __name__=="__main__":
    pass
