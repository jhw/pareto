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

@resource(suffix="action-mapping")
def QueueActionMapping(batch=1, **kwargs):
    funcarn=fn_getatt("%s-action" % kwargs["name"], "Arn")
    eventsource=fn_getatt(kwargs["name"], "Arn")
    props={"FunctionName": funcarn,
           "EventSourceArn": eventsource,
           "BatchSize": batch}
    return "AWS::Lambda::EventSourceMapping", props

@event_mapping_permissions(EventMappingPermissions)
def synth_queue(**kwargs):
    template=Template(resources=[Queue(**kwargs)])
    if "action" in kwargs:
        template.resources.append(QueueActionMapping(**kwargs))
    return template

if __name__=="__main__":
    pass
