from pareto.components import *

from pareto.components.template import synth_template

TypeFilters={
    "api": lambda x: x["type"]=="function" and "api" in x,
    "action": lambda x: x["type"]=="function" and "api" not in x,
    "trigger": lambda x: x["type"]!="function"
    }

def synth_stack(config):
    components=config.pop("components")
    stack={}
    for key in TypeFilters.keys():
        config["components"]=[component
                              for component in components
                              if TypeFilters[key](component)]
        stack["%ss" % key]=synth_template(config)
    stack["dashboards"]={}
    stack["master"]={}
    return stack

if __name__=="__main__":
    pass
