from pareto.components import *

def synth_stack(**kwargs):
    @resource(suffix="stack")
    def Stack(**kwargs):
        params, url = {}, None
        props={"Parameters": kwargs["params"],
               "TemplateURL": url}
        return "AWS::Cloudformation::Stack", props    
    struct={"parameters": [],
            "resources": [Stack(**kwargs)],
            "outputs": []}
    return {k:v for k, v in struct.items()
            if v!=[]}
    
if __name__=="__main__":
    pass
