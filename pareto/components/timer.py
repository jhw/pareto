from pareto.components import *

@resource()
def EventRule(**kwargs):
    action={"Id": resource_name(kwargs),
            "Input": json.dumps(kwargs["payload"]),
            "Arn": ref("%s-arn" % kwargs["action"])}
    expr="rate(%s)" % kwargs["rate"]
    props={"ScheduleExpression": expr,
           "Targets": [action]}
    return "AWS::Events::Rule", props

@resource(suffix="permission")
def ActionPermission(**kwargs):
    source=fn_getatt(kwargs["name"], "Arn")
    target=ref("%s-arn" % kwargs["action"])
    props={"Action": "lambda:InvokeFunction",
           "FunctionName": target,
           "Principal": "events.amazonaws.com",
           "SourceArn": source}
    return "AWS::Lambda::Permission", props

def synth_timer(template, **kwargs):
    template.update(Parameters=parameter("%s-arn" % kwargs["action"]),
                    Resources=[EventRule(**kwargs),
                               ActionPermission(**kwargs)])

if __name__=="__main__":
    pass
