from pareto.components import *

ParamNames=yaml.safe_load("""
- staging-bucket
""")

@resource(suffix="layer")
def Layer(**kwargs):
    content={"S3Key": ref("%s-layer-staging-key" % kwargs["name"]),
             "S3Bucket": ref("staging-bucket")}
    props={"Content": content,
           "CompatibleRuntimes": [ref("runtime-version")]}
    return "AWS::Lambda::LayerVersion", props
    
@output(suffix="layer-arn")
def LayerArn(**kwargs):
    return ref("%s-layer" % kwargs["name"])

def synth_layer(template, **kwargs):
    paramnames=ParamNames+["%s-layer-staging-key" % kwargs["name"]]
    template.update(Parameters=[parameter(paramname)
                                for paramname in paramnames],
                    Resources=Layer(**kwargs),
                    Outputs=LayerArn(**kwargs))

if __name__=="__main__":
    pass
