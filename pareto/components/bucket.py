from pareto.components import *

from pareto.components.action import *

@resource()
def Bucket(event={"type":  "s3:ObjectCreated:*"},
           **kwargs):
    def lambda_config(kwargs, event):
        funcarn=fn_getatt("%s-action" % kwargs["name"], "Arn")
        rules=[{"Name": "prefix",
                "Value": kwargs["path"]}]
        return {"Event": event["type"],
                "Function": funcarn,
                "Filter": {"S3Key": {"Rules": rules}}}
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

def add_action(kwargs, template):
    template["resources"]+=[Action(**kwargs),
                            ActionRole(**kwargs),
                            ActionDeadLetterQueue(**kwargs),
                            ActionVersion(**kwargs),
                            ActionEventConfig(**kwargs),
                            BucketActionPermission(**kwargs)]

def synth_bucket(**kwargs):
    template=Template(resources=[Bucket(**kwargs)])
    if "action" in kwargs:
        add_action(kwargs, template)
    return template

def synth_website(**kwargs):
    def website_config(index="index.json"):
        corsrules=[{"AllowedMethods": ["GET"],
                    "AllowedOrigins": ["*"]}]
        corsconfig={"CorsRules": corsrules}
        websiteconfig={"IndexDocument": index}
        return {"AccessControl": "PublicRead",
                "CorsConfiguration": corsconfig,
                "WebsiteConfiguration": websiteconfig}
    @output(suffix="url")
    def BucketUrl(**kwargs):
        return fn_getatt(kwargs["name"], "WebsiteURL")
    @resource(suffix="policy")
    def BucketPolicy(**kwargs):
        def policy_document(kwargs):
            resource=fn_sub("arn:aws:s3:::${bucket_name}/*",
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
    template=Template(resources=[Bucket(**kwargs),
                                 BucketPolicy(**kwargs)],
                      outputs=[BucketUrl(**kwargs)])
    if "action" in kwargs:
        add_action(kwargs, template)
    return template

if __name__=="__main__":
    pass
