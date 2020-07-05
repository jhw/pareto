from pareto.components import *

@trim_template
def synth_queue(**kwargs):
    @resource()
    def Queue(**kwargs):        
        props={"QueueName": resource_id(kwargs)}
        return "AWS::SQS::Queue", props
    def LambdaMapping(**kwargs):
        suffix="%s-mapping" % kwargs["action"]["name"]
        @resource(suffix)
        def LambdaMapping(batch=1, **kwargs):
            funcarn=ref("%s-arn" % kwargs["action"]["name"])
            eventsource=fn_getatt(kwargs["name"], "Arn")
            props={"FunctionName": funcarn,
                   "EventSourceArn": eventsource,
                   "BatchSize": batch}
            return "AWS::Lambda::EventSourceMapping", props
        return LambdaMapping(**kwargs)
    struct={"resources": [Queue(**kwargs)]}
    if "action" in kwargs:
        actionarn=parameter("%s-arn" % kwargs["action"]["name"])
        struct.setdefault("parameters", [])
        struct["parameters"].append(actionarn)
        struct["resources"].append(LambdaMapping(**kwargs))
    return struct

if __name__=="__main__":
    pass
