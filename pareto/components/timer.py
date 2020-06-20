from pareto.components import *

def synth_timer(**kwargs):
    @resource()
    def EventRule(**kwargs):
        """
        - single action for the minute but could be an array
        """
        action={"Id": global_name(kwargs),
                "Input": json.dumps(kwargs["payload"]),
                "Arn": fn_getatt(kwargs["action"]["name"], "Arn")}
        expr="rate(%s)" % kwargs["rate"]
        props={"ScheduleExpression": expr,
               "Targets": [action]}
        return "AWS::Events::Rule", props
    def LambdaPermission(**kwargs):
        suffix="%s-permission" % kwargs["action"]["name"]
        @resource(suffix=suffix)
        def LambdaPermission(**kwargs):
            arn=fn_getatt(kwargs["action"]["name"], "Arn")
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
