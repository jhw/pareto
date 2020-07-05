from pareto.components import *

TemplateUrl="https://s3.%s.amazonaws.com/%s/%s-%s/templates/%s.yaml"

def synth_stack(**kwargs):
    @resource(suffix="stack")
    def Stack(**kwargs):
        url=TemplateUrl % (kwargs["region"],
                           kwargs["bucket"],
                           kwargs["app"],
                           kwargs["stage"],
                           kwargs["name"])
        props={"Parameters": kwargs["params"],
               "TemplateURL": url}
        return "AWS::Cloudformation::Stack", props    
    return Template(resources=[Stack(**kwargs)])
    
if __name__=="__main__":
    pass
