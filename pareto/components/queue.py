from pareto.components import *

def synth_queue(**kwargs):
    @resource()
    def Queue(**kwargs):        
        props={"QueueName": resource_id(kwargs)}
        return "AWS::SQS::Queue", props
    @output(suffix="arn")
    def QueueArn(**kwargs):
        return fn_getatt(kwargs["name"], "Arn")
    def LambdaMapping(**kwargs):
        suffix="%s-mapping" % kwargs["action"]["name"]
        @resource(suffix)
        def LambdaMapping(batch=1, **kwargs):
            funcname=fn_getatt(kwargs["action"]["name"], "Arn")
            eventsource=fn_getatt(kwargs["name"], "Arn")
            props={"FunctionName": funcname,
                   "EventSourceArn": eventsource,
                   "BatchSize": batch}
            return "AWS::Lambda::EventSourceMapping", props
        return LambdaMapping(**kwargs)
    resources=[Queue(**kwargs)]
    outputs=[QueueArn(**kwargs)]
    if "action" in kwargs:
        resources.append(LambdaMapping(**kwargs))
    return {"resources": resources,
            "outputs": outputs}

if __name__=="__main__":
    pass
