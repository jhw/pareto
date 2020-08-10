from pareto.components import *

@resource(suffix="layer")
def Layer(**kwargs):
    content={"S3Key": str(kwargs["staging"]),
             "S3Bucket": kwargs["bucket"]}
    props={"Content": content,
           "CompatibleRuntimes": ["python%s" % kwargs["runtime"]]}
    return "AWS::Lambda::LayerVersion", props
    
@output(suffix="layer-arn")
def LayerArn(**kwargs):
    # return fn_getatt("%s-layer" % kwargs["name"], "Arn")
    return ref("%s-layer" % kwargs["name"])

def synth_layer(template, **kwargs):
    template.update(Resources=Layer(**kwargs),
                    Outputs=LayerArn(**kwargs))

if __name__=="__main__":
    pass
