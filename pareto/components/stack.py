from pareto.components import *

from pareto.components.template import synth_template

TypeFilters={
    "api": lambda x: x["type"]=="function" and "api" in x,
    "action": lambda x: x["type"]=="function" and "api" not in x,
    "trigger": lambda x: x["type"]!="function"
    }

def synth_stack(config):
    @resource(suffix="stack")
    def NestedStack(**kwargs):
        params, url = {}, None
        props={"Parameters": params,
               "TemplateURL": url}
        return "AWS::Cloudformation::Stack", props    
    def add_component_groups(templates, components):
        for key in TypeFilters.keys():
            config["components"]=[component
                                  for component in components
                                  if TypeFilters[key](component)]
            templates["%ss" % key]=synth_template(config)
    def init_dashboards(templates):
        struct={"parameters": [],
                "resources": [],
                "outputs": []}
        return {k:v for k, v in struct.items()
                if v!=[]}
    def add_dashboards(templates):
        templates["dashboards"]=init_dashboards(templates)
    def init_master(templates):
        struct={"parameters": [],
                "resources": [NestedStack(name="hello-world")],
                "outputs": []}
        return {k:v for k, v in struct.items()
                if v!=[]}
    def add_master(templates):
        templates["master"]=init_master(templates)
    templates={}
    add_component_groups(templates, config.pop("components"))
    add_dashboards(templates)
    add_master(templates)
    return templates

if __name__=="__main__":
    pass
