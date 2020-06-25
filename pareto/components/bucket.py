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
        arn=fn_getatt(action["name"], "Arn")
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
        props={"BucketName": global_name(kwargs)}
        if is_website(kwargs):
            props.update(website_config())
        if "actions" in kwargs:
            props.update(notifications_configs(event, kwargs))
        return "AWS::S3::Bucket", props
    def LambdaPermission(kwargs, action):
        suffix="%s-permission" % action["name"]
        @resource(suffix=suffix)
        def LambdaPermission(**kwargs):
            eventsource=fn_getatt(kwargs["name"], "Arn")
            funcname=fn_getatt(action["name"], "Arn")
            props={"Action": "lambda:InvokeFunction",
                   "FunctionName": funcname,
                   "Principal": "s3.amazonaws.com",
                   "SourceArn": eventsource}
            return "AWS::Lambda::Permission", props
        return LambdaPermission(**kwargs)
    @resource(suffix="policy")
    def BucketPolicy(**kwargs):
        def policy_document(kwargs):
            resource=fn_join(["arn:aws:s3:::",
                              ref(kwargs["name"]),
                              "/*"])
            statement=[{"Action": "s3:GetObject",
                        "Effect": "Allow",
                        "Principal": "*",
                        "Resource": resource}]
            return {"Statement": statement,
                    "Version": "2012-10-17"}
        props={"Bucket": ref(kwargs["name"]),
               "PolicyDocument": policy_document(kwargs)}
        return "AWS::S3::BucketPolicy", props
    @output(suffix="url")
    def BucketUrl(**kwargs):
        return fn_getatt(kwargs["name"], "WebsiteURL")
    resources, outputs = [Bucket(**kwargs)], []
    if "actions" in kwargs:
        resources+=[LambdaPermission(kwargs, action)
                    for action in kwargs["actions"]]
    if is_website(kwargs):
        resources.append(BucketPolicy(**kwargs))        
        outputs.append(BucketUrl(**kwargs))
    return {"resources": resources,
            "outputs": outputs}

if __name__=="__main__":
    pass
