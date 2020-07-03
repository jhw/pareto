from pareto.components import *

def synth_bucket(**kwargs):
    def is_website(kwargs):
        return "website" in kwargs and kwargs["website"]
    def website_config(index="index.json"):
        corsrules=[{"AllowedMethods": ["GET"],
                    "AllowedOrigins": ["*"]}]
        corsconfig={"CorsRules": corsrules}
        websiteconfig={"IndexDocument": index}
        return {"AccessControl": "PublicRead",
                "CorsConfiguration": corsconfig,
                "WebsiteConfiguration": websiteconfig}
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
        props={"BucketName": resource_id(kwargs)}
        if is_website(kwargs):
            props.update(website_config())
        if "actions" in kwargs:
            props.update(notifications_configs(event, kwargs))
        return "AWS::S3::Bucket", props
    @output(suffix="url")
    def BucketUrl(**kwargs):
        return fn_getatt(kwargs["name"], "WebsiteURL")
    @output(suffix="arn")
    def BucketArn(**kwargs):
        return fn_getatt(kwargs["name"], "Arn")
    def LambdaPermission(kwargs, action):
        suffix="%s-permission" % action["name"]
        @resource(suffix=suffix)
        def LambdaPermission(**kwargs):
            """
            - https://aws.amazon.com/premiumsupport/knowledge-center/unable-validate-circular-dependency-cloudformation/
            - Fn::GetAtt Arn doesn't work for S3 lambda notifications :-(
            - NB also recommends using SourceAccount as account not included in S3 arn format
            """
            eventsource="arn:aws:s3:::%s" % resource_id(kwargs)
            funcname=fn_getatt(action["name"], "Arn")
            props={"Action": "lambda:InvokeFunction",
                   "FunctionName": funcname,
                   "SourceAccount": fn_sub("${AWS::AccountId}"),
                   "SourceArn": eventsource,
                   "Principal": "s3.amazonaws.com"}
            return "AWS::Lambda::Permission", props
        return LambdaPermission(**kwargs)
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
    struct={"parameters": [],
            "resources": [Bucket(**kwargs)],
            "outputs": [BucketArn(**kwargs)]}
    if "actions" in kwargs:
        for action in kwargs["actions"]:
            struct["parameters"].append(parameter("%s-arn" % action["name"]))
            struct["resources"].append(LambdaPermission(kwargs, action))
    if is_website(kwargs):
        struct["resources"].append(BucketPolicy(**kwargs))        
        struct["outputs"].append(BucketUrl(**kwargs))
    return {k:v for k, v in struct.items()
            if v!=[]}

if __name__=="__main__":
    pass
