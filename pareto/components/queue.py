from pareto.components import *

@resource()
def Queue(**kwargs):        
    props={"QueueName": "%s.fifo" % resource_name(kwargs),
           "FifoQueue": True}
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
    template.update(Resources=Queue(**kwargs))
    if "action" in kwargs:
        template.update(Parameters=parameter("%s-arn" % kwargs["action"]),
                        Resources=QueueMapping(**kwargs))

if __name__=="__main__":
    pass
