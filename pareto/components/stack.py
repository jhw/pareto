from pareto.components import *

TemplateUrl="https://s3.%s.amazonaws.com/%s/%s-%s/templates/%s.json"

def synth_stack(**kwargs):
    @resource() # NB no suffix
    def Stack(**kwargs):
        url=TemplateUrl % (kwargs["region"],
                           kwargs["bucket"],
                           kwargs["app"],
                           kwargs["stage"],
                           kwargs["name"])
        props={"TemplateURL": url}
        if ("params" in kwargs and
            kwargs["params"]!={}):
            props["Parameters"]=kwargs["params"]
        return "AWS::CloudFormation::Stack", props    
    return Template(resources=[Stack(**kwargs)])
    
if __name__=="__main__":
    pass
