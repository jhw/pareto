from pareto.components import *

from pareto.components.template import synth_template

TypeFilters={
    "api": lambda x: x["type"]=="function" and "api" in x,
    "action": lambda x: x["type"]=="function" and "api" not in x,
    "trigger": lambda x: x["type"]!="function"
    }

def synth_env(config):
    def add_components(config, templates):
        components=config.pop("components")
        for key in TypeFilters.keys():
            config["components"]=[component
                                  for component in components
                                  if TypeFilters[key](component)]
            templates["%ss" % key]=synth_template(config)
    def add_master(config, templates):
        config["components"]=[{"type": "stack",
                               "name": key,
                               "params": {"foo": "bar"}}
                              for key in templates.keys()]
        templates["master"]=synth_template(config)
    templates={}
    add_components(config, templates)
    add_master(config, templates)
    return templates

if __name__=="__main__":
    pass
