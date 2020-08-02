from pareto.components import *

@resource()
def EventRule(**kwargs):
    action={"Id": resource_name(kwargs),
            "Input": json.dumps(kwargs["payload"]),
            "Arn": fn_getatt("%s-action" % kwargs["name"], "Arn")}
    expr="rate(%s)" % kwargs["rate"]
    props={"ScheduleExpression": expr,
           "Targets": [action]}
    return "AWS::Events::Rule", props

@resource(suffix="action-permission")
def EventActionPermission(**kwargs):
    eventsource=fn_getatt(kwargs["name"], "Arn")
    funcarn=fn_getatt("%s-action" % kwargs["name"], "Arn")
    props={"Action": "lambda:InvokeFunction",
           "FunctionName": funcarn,
           "Principal": "events.amazonaws.com",
           "SourceArn": eventsource}
    return "AWS::Lambda::Permission", props

@output(suffix="arn")
def EventArn(**kwargs):
    return fn_getatt(kwargs["name"], "Arn")
    
def synth_timer(**kwargs):
    return Template(resources=[EventRule(**kwargs),
                               EventActionPermission(**kwargs)],
                    outputs=[EventArn(**kwargs)])

if __name__=="__main__":
    pass
