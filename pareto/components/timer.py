from pareto.components import *

def synth_timer(**kwargs):
    @resource()
    def EventRule(**kwargs):
        action={"Id": resource_id(kwargs),
                "Input": json.dumps(kwargs["payload"]),
                "Arn": fn_getatt(kwargs["action"]["name"], "Arn")}
        expr="rate(%s)" % kwargs["rate"]
        props={"ScheduleExpression": expr,
               "Targets": [action]}
        return "AWS::Events::Rule", props
    @output(suffix="arn")
    def EventRuleArn(**kwargs):
        return fn_getatt(kwargs["name"], "Arn")
    def LambdaPermission(**kwargs):
        suffix="%s-permission" % kwargs["action"]["name"]
        @resource(suffix=suffix)
        def LambdaPermission(**kwargs):
            eventsource=fn_getatt(kwargs["name"], "Arn")
            funcname=fn_getatt(kwargs["action"]["name"], "Arn")
            props={"Action": "lambda:InvokeFunction",
                   "FunctionName": funcname,
                   "Principal": "events.amazonaws.com",
                   "SourceArn": eventsource}
            return "AWS::Lambda::Permission", props
        return LambdaPermission(**kwargs)
    resources=[EventRule(**kwargs),
               LambdaPermission(**kwargs)]
    outputs=[EventRuleArn(**kwargs)]
    return {"resources": resources,
            "outputs": outputs}

if __name__=="__main__":
    pass
