from pareto.components import *

from pareto.components.template import synth_template

TypeFilters={
    "api": lambda x: x["type"]=="function" and "api" in x,
    "action": lambda x: x["type"]=="function" and "api" not in x,
    "trigger": lambda x: x["type"]!="function"
    }

def synth_stack(config):
    @resource()
    def Stack(**kwargs):
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
    def add_master(templates):
        templates["master"]={}
    def add_dashboard(templates):
        templates["dashboards"]={}
    templates={}
    add_component_groups(templates, config.pop("components"))
    return templates

if __name__=="__main__":
    pass
