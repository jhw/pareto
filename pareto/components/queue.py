from pareto.components import *

from pareto.components.function import *

def synth_queue(**kwargs):
    @resource()
    def Queue(**kwargs):        
        props={"QueueName": resource_name(kwargs)}
        return "AWS::SQS::Queue", props
    def LambdaMapping(**kwargs):
        suffix="%s-mapping" % kwargs["name"]
        @resource(suffix)
        def LambdaMapping(batch=1, **kwargs):
            funcarn=fn_getatt("%s-action" % kwargs["name"], "Arn")
            eventsource=fn_getatt(kwargs["name"], "Arn")
            props={"FunctionName": funcarn,
                   "EventSourceArn": eventsource,
                   "BatchSize": batch}
            return "AWS::Lambda::EventSourceMapping", props
        return LambdaMapping(**kwargs)
    template=Template(resources=[Queue(**kwargs)])
    if "action" in kwargs:
        template["resources"]+=[Function(**kwargs),
                                FunctionRole(**kwargs),
                                FunctionDeadLetterQueue(**kwargs),
                                FunctionVersion(**kwargs),
                                FunctionEventConfig(**kwargs),
                                LambdaMapping(**kwargs)]
    return template

if __name__=="__main__":
    pass
