from pareto.components import *

from pareto.components.action import *

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

"""
- option to include specific sqs permissions to enable lambda to poll sqs for new messages
- see tables (dynamodb), also any other resource which uses event mapping (kinesis)
- not currently implemented because default `sqs:*` permissions are applied at the ActionRole level to enable all actions to push to dead letter queues (created by default)
"""

def event_mapping_permissions(fn):
    def wrapped(**kwargs):
        if "action" in kwargs:
            kwargs["action"].setdefault("permissions", [])
            # add custom permissions here
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
