from pareto.components import *

ParamNames=yaml.safe_load("""
- app-name
- stage-name
""")

@resource()
def Timer(**kwargs):
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
    paramnames=ParamNames+["%s-arn" % kwargs["action"]]
    template.update(Parameters=[parameter(paramname)
                                for paramname in paramnames],
                    Resources=[Timer(**kwargs),
                               ActionPermission(**kwargs)])

if __name__=="__main__":
    pass
