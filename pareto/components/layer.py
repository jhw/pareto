from pareto.components import *

@resource(suffix="layer")
def Layer(**kwargs):
    content={"S3Key": ref("%s-layer-staging-key" % kwargs["name"]),
             "S3Bucket": ref("staging-bucket")}
    props={"Content": content,
           "CompatibleRuntimes": [ref("python-runtime-version")]}
    return "AWS::Lambda::LayerVersion", props
    
@output(suffix="layer-arn")
def LayerArn(**kwargs):
    return ref("%s-layer" % kwargs["name"])

def synth_layer(template, **kwargs):
    template.update(Resources=Layer(**kwargs),
                    Outputs=LayerArn(**kwargs))

if __name__=="__main__":
    pass
