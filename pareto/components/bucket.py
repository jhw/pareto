from pareto.components import *

def synth_bucket(**kwargs):
    def is_website(kwargs):
        return "website" in kwargs and kwargs["website"]
    def website_config():
        corsrules=[{"AllowedMethods": ["GET"],
                    "AllowedOrigins": ["*"]}]
        corsconfig={"CorsRules": corsrules}
        """
        - index doc required I believe, even if not specified
        """
        websiteconfig={"IndexDocument": "index.json"}
        return {"AccessControl": "PublicRead",
                "CorsConfiguration": corsconfig,
                "WebsiteConfiguration": websiteconfig}
    def lambda_notification_config(target):
        arn=fn_getatt(target["name"], "Arn")
        rules=[{"Name": "prefix",
                "Value": target["path"]}]
        """
        - event hardcoded as `s3:ObjectCreated` for now
        - could become an option later
        """
        return {"Event": "s3:ObjectCreated:*",
                "Function": arn,
                "Filter": {"S3Key": {"Rules": rules}}}
    def notifications_configs(kwargs):
        lambdaconfigs=[lambda_notification_config(target)
                      for target in kwargs["targets"]]
        notifications={"LambdaConfigurations": lambdaconfigs}
        return {"NotificationConfiguration": notifications}
    @resource()
    def Bucket(**kwargs):
        props={"BucketName": global_name(kwargs)}
        if is_website(kwargs):
            props.update(website_config())
        if "targets" in kwargs:
            props.update(notifications_configs(kwargs))
        return "AWS::S3::Bucket", props
    def LambdaPermission(kwargs, target):
        suffix="%s-permission" % target["name"]
        @resource(suffix=suffix)
        def LambdaPermission(**kwargs):
            arn=fn_getatt(target["name"], "Arn")
            props={"Action": "lambda:InvokeFunction",
                   "FunctionName": arn,
                   "Principal": "s3.amazonaws.com"}
            return "AWS::Lambda::Permission", props
        return LambdaPermission(**kwargs)
    @resource(suffix="policy")
    def BucketPolicy(**kwargs):
        def policy_document(kwargs):
            resource=fn_join(["arn:aws:s3:::",
                              ref(kwargs["name"]),
                              "/*"])
            statement=[{"Action": "s3:GetObject",
                        "Effect": "allow",
                        "Principal": "*",
                        "Resource": resource,
                        "Sid": "PublicReadForGetBucketObjects"}]
            return {"Statement": statement,
                    "Version": "2012-10-17"}
        props={"Bucket": ref(kwargs["name"]),
               "PolicyDocument": policy_document(kwargs)}
        return "AWS::S3::BucketPolicy", props
    @output(suffix="url")
    def BucketUrl(**kwargs):
        return fn_getatt(kwargs["name"], "WebsiteURL")
    resources, outputs = [Bucket(**kwargs)], []
    if "targets" in kwargs:
        resources+=[LambdaPermission(kwargs, target)
                    for target in kwargs["targets"]]
    if is_website(kwargs):
        resources.append(BucketPolicy(**kwargs))        
        outputs.append(BucketUrl(**kwargs))
    return {"resources": resources,
            "outputs": outputs}

if __name__=="__main__":
    pass
