from pareto.components import *

from pareto.components.bucket import synth_bucket
from pareto.components.dashboard import synth_dashboard
from pareto.components.function import synth_function
from pareto.components.queue import synth_queue
from pareto.components.stack import synth_stack
from pareto.components.table import synth_table
from pareto.components.timer import synth_timer

TypeFilters={
    "api": lambda x: x["type"]=="function" and "api" in x,
    "action": lambda x: x["type"]=="function" and "api" not in x,
    "trigger": lambda x: x["type"]!="function"
    }

def add_component_groups(config, templates, filters=TypeFilters):
    def init_component(config, component):
        component.update({k:config[k]
                          for k in config
                          if k!="components"})
        return component
    def group_components(config, filters):
        return {key: [init_component(config, component)
                      for component in config["components"]
                      if filters[key](component)]
                for key in filters}
    def init_template(components):
        template=Template()
        for kwargs in components:
            fn=eval("synth_%s" % kwargs["type"])                
            component=fn(**kwargs)
            template.update(component)
        return template.render()
    groups=group_components(config, filters)
    for key, group in groups.items():
        templates[key]=init_template(group)

def add_dashboards(config, templates, filters=TypeFilters):
    def init_group(config, components):
        group={k:config[k]
               for k in config
               if k!="components"}
        group["components"]=components
        return group
    def filter_types(components):
        return list(set([component["type"]
                         for component in components]))
    def init_groups(config, filters):
        groups={}
        for key, filterfn in filters.items():
            components=[component
                         for component in config["components"]
                         if filterfn(component)]
            if "function" not in filter_types(components):
                continue
            group=init_group(config, components)
            groups[key]=group
        return groups
    groups=init_groups(config, filters)
    template=Template()    
    for key, kwargs in groups.items():
        kwargs["name"]="%s-dashboard" % key
        dashboard=synth_dashboard(**kwargs)
        template.update(dashboard)
    templates["dashboard"]=template.render()
        
def add_master(config, templates, filters=TypeFilters):
    def stack_id(stackname):
        return logical_id("%s-stack" % stackname)
    def output_ref(name, attr):
        return {"Fn::GetAtt": [name, "Outputs.%s" % attr]}
    def filter_outputs(templates, filters):        
        outputs={}
        for tempname, template in templates.items():
            if tempname in filters:
                outputs.update({paramname: tempname
                                for paramname in template["Outputs"]
                                if "Outputs" in template})
        return outputs
    def format_params(paramnames, outputs):
        return {paramname: output_ref(stack_id(outputs.pop(paramname)),
                                      paramname)
                for paramname in list(paramnames)}
    def init_params(template, outputs):
        return format_params(template["Parameters"].keys(),
                             outputs) if "Parameters" in template else {}
    def init_stack(config, tempname, template, outputs):
        stack={}
        stack.update({k:config[k]
                      for k in config
                      if k!="components"})
        params=init_params(template,
                           outputs)
        stack.update({"name": tempname,
                      "params": params})
        return stack
    def format_outputs(outputs):
        return {paramname: {"Value": output_ref(stack_id(tempname),
                                                paramname)}         
                for paramname, tempname in outputs.items()}        
    def init_template(config, templates, filters):
        outputs=filter_outputs(templates, filters)
        components=[init_stack(config, tempname, template, outputs)
                    for tempname, template in templates.items()]
        template=Template()
        for kwargs in components:
            stack=synth_stack(**kwargs)
            template.update(stack)
        template["outputs"]=format_outputs(outputs)
        return template.render()
    templates["master"]=init_template(config, templates, filters)
        
def synth_env(config):
    templates={}
    for attr in ["component_groups",
                 "dashboards",
                 "master"]:
        fn=eval("add_%s" % attr)
        fn(config, templates)
    return templates

if __name__=="__main__":
    pass
