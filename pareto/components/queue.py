from pareto.components import *

def synth_queue(**kwargs):
    @resource()
    def Queue(**kwargs):        
        props={"QueueName": resource_id(kwargs)}
        return "AWS::SQS::Queue", props
    """
    - don't *think* you need a LambdaPermission if you have a LambdaMapping
    - (think LambdaPermission is only for primitives without EventSourceMapping, ie S3, SNS)
    """
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
    if "action" in kwargs:
        resources.append(LambdaMapping(**kwargs))
    return {"resources": resources}

if __name__=="__main__":
    pass
