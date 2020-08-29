from pareto.components import *

ParamNames=yaml.safe_load("""
- app-name
- stage-name
""")

@resource()
def Queue(**kwargs):
    props={"QueueName": resource_name(kwargs)}
    return "AWS::SQS::Queue", props

@resource(suffix="mapping")
def QueueMapping(batch=1, **kwargs):
    target=ref("%s-arn" % kwargs["action"])
    source=fn_getatt(kwargs["name"], "Arn")
    props={"FunctionName": target,
           "EventSourceArn": source,
           "BatchSize": batch}
    return "AWS::Lambda::EventSourceMapping", props

def synth_queue(template, **kwargs):
    template.update(Parameters=[parameter(paramname)
                                for paramname in ParamNames],
                    Resources=Queue(**kwargs))
    if "action" in kwargs:
        template.update(Parameters=parameter("%s-arn" % kwargs["action"]),
                        Resources=QueueMapping(**kwargs))

if __name__=="__main__":
    pass
