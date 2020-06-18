from pareto.components import *

def synth_timer(**kwargs):
    @resource()
    def EventRule(**kwargs):
        """
        - single target for the minute but could be an array
        """
        target={"Id": global_name(kwargs),
                "Input": json.dumps(kwargs["payload"]),
                "Arn": fn_getatt(kwargs["target"], "Arn")}
        expr="rate(%s)" % kwargs["rate"]
        props={"ScheduleExpression": expr,
               "Targets": [target]}
        return "AWS::Events::Rule", props
    def LambdaPermission(**kwargs):
        suffix="%s-permission" % kwargs["target"]
        @resource(suffix=suffix)
        def LambdaPermission(**kwargs):
            arn=fn_getatt(kwargs["target"], "Arn")
            props={"Action": "lambda:InvokeFunction",
                   "FunctionName": arn,
                   "Principal": "events.amazonaws.com"}
            return "AWS::Lambda::Permission", props
        return LambdaPermission(**kwargs)
    resources=[EventRule(**kwargs),
               LambdaPermission(**kwargs)]
    return {"resources": resources}

if __name__=="__main__":
    pass
