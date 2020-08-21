from pareto.components import *

TemplateUrl="https://s3.${region}.amazonaws.com/${staging_bucket}/${app_name}/templates/%s.json"

@resource()
def Stack(**kwargs):
    url=fn_sub(TemplateUrl % kwargs["name"],
               {"region": ref("region"),
                "staging_bucket": ref("staging-bucket"),
                "app_name": ref("app_name")})
    props={"TemplateURL": url}
    if ("params" in kwargs and
        kwargs["params"]!={}):
        props["Parameters"]=kwargs["params"]
    return "AWS::CloudFormation::Stack", props

def synth_stack(template, **kwargs):
    template.update(Resources=Stack(**kwargs))
    
if __name__=="__main__":
    pass
