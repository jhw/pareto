from pareto.components import *

from pareto.components.action import *

EventMappingPermissions=yaml.load("""
- sqs:ReceiveMessage
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

def event_mapping_permissions(fn):
    def wrapped(**kwargs):
        if "action" in kwargs:
            kwargs["action"].setdefault("permissions", [])
            permissions=kwargs["action"]["permissions"]
            if "sqs:*" not in permissions:
                permissions+=EventMappingPermissions
        return fn(**kwargs)
    return wrapped

@event_mapping_permissions
def synth_queue(**kwargs):
    template=Template(resources=[Queue(**kwargs)])
    if "action" in kwargs:
        template["resources"]+=[Action(**kwargs),
                                ActionRole(**kwargs),
                                ActionDeadLetterQueue(**kwargs),
                                ActionVersion(**kwargs),
                                ActionEventConfig(**kwargs),
                                QueueActionMapping(**kwargs)]
    return template

if __name__=="__main__":
    pass
