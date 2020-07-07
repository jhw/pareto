from pareto.components import *

def synth_queue(**kwargs):
    @resource()
    def Queue(**kwargs):        
        props={"QueueName": resource_name(kwargs)}
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
    template=Template(resources=[Queue(**kwargs)])
    if "action" in kwargs:
        actionarn=parameter("%s-arn" % kwargs["action"]["name"])
        template.setdefault("parameters", [])
        template["parameters"].append(actionarn)
        template["resources"].append(LambdaMapping(**kwargs))
    return template

if __name__=="__main__":
    pass
