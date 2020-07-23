from pareto.components import *

from pareto.components.function import *

def synth_timer(**kwargs):
    @resource()
    def EventRule(**kwargs):
        action={"Id": resource_name(kwargs),
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
            eventsource=fn_getatt(kwargs["name"], "Arn")
            funcarn=fn_getatt("%s-action" % kwargs["name"], "Arn")
            props={"Action": "lambda:InvokeFunction",
                   "FunctionName": funcarn,
                   "Principal": "events.amazonaws.com",
                   "SourceArn": eventsource}
            return "AWS::Lambda::Permission", props
        return LambdaPermission(**kwargs)
    return Template(resources=[Function(**kwargs),
                               FunctionRole(**kwargs),
                               FunctionDeadLetterQueue(**kwargs),
                               FunctionVersion(**kwargs),
                               FunctionEventConfig(**kwargs),
                               EventRule(**kwargs),
                               LambdaPermission(**kwargs)])

if __name__=="__main__":
    pass
