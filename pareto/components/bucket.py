from pareto.components import *

def lambda_notification_config(action, event):
    arn=ref("%s-arn" % action["name"])
    rules=[{"Name": "prefix",
            "Value": action["path"]}]
    return {"Event": event["type"],
            "Function": arn,
            "Filter": {"S3Key": {"Rules": rules}}}

def notifications_configs(event, kwargs):
    lambdaconfigs=[lambda_notification_config(action, event)
                   for action in kwargs["actions"]]
    notifications={"LambdaConfigurations": lambdaconfigs}
    return {"NotificationConfiguration": notifications}

@resource()
def Bucket(event={"type":  "s3:ObjectCreated:*"},
           **kwargs):
    props={"BucketName": resource_name(kwargs)}
    if "actions" in kwargs:
        props.update(notifications_configs(event, kwargs))
    return "AWS::S3::Bucket", props

def LambdaPermission(kwargs, action):
    suffix="%s-permission" % action["name"]
    @resource(suffix=suffix)
    def LambdaPermission(**kwargs):
        """
        - https://aws.amazon.com/premiumsupport/knowledge-center/unable-validate-circular-dependency-cloudformation/
        - Fn::GetAtt Arn doesn't work for S3 lambda notifications :-(
        - NB also recommends using SourceAccount as account not included in S3 arn format
        """
        eventsource="arn:aws:s3:::%s" % resource_name(kwargs)
        funcname=ref("%s-arn" % action["name"])
        props={"Action": "lambda:InvokeFunction",
               "FunctionName": funcname,
               "SourceAccount": fn_sub("${AWS::AccountId}"),
               "SourceArn": eventsource,
               "Principal": "s3.amazonaws.com"}
        return "AWS::Lambda::Permission", props
    return LambdaPermission(**kwargs)

def synth_bucket(**kwargs):
    template=Template(resources=[Bucket(**kwargs)])
    def add_action(kwargs, action, template):
        template["parameters"].append(parameter("%s-arn" % action["name"]))
        template["resources"].append(LambdaPermission(kwargs, action))
    if "actions" in kwargs:
        for action in kwargs["actions"]:
            add_action(kwargs, action, template)
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
    def add_action(kwargs, action, template):
        template["parameters"].append(parameter("%s-arn" % action["name"]))
        template["resources"].append(LambdaPermission(kwargs, action))
    if "actions" in kwargs:
        for action in kwargs["actions"]:
            add_action(kwargs, action, template)
    return template

if __name__=="__main__":
    pass
