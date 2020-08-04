from pareto.components import *

EventMappingPermissions=yaml.load("""
- sqs:ReceiveMessage
- sqs:DeleteMessage
- sqs:GetQueueAttributes
""", Loader=yaml.FullLoader)

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

@event_mapping_permissions(EventMappingPermissions)
def synth_queue(**kwargs):
    template=Template(resources=[Queue(**kwargs)])
    if "action" in kwargs:
        template.parameters.append(parameter("%s-arn" % kwargs["action"]))
        template.resources.append(QueueMapping(**kwargs))
    return template

if __name__=="__main__":
    pass
