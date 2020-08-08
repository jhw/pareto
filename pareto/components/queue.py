from pareto.components import *

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

def synth_queue(**kwargs):
    template=Template(Resources=[Queue(**kwargs)])
    if "action" in kwargs:
        template.update(Parameters=[parameter("%s-arn" % kwargs["action"])],
                        Resources=[QueueMapping(**kwargs)])
    return template

if __name__=="__main__":
    pass
