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

def add_components(config, templates):
    def init_template(config):
        template=Template()
        for item in config["components"]:
            item.update({k:config[k]
                         for k in config
                         if k!="components"})
            fn=eval("synth_%s" % item["type"])                
            component=fn(**item)
            template.update(component)
        return template.render()
    components=config.pop("components")
    for typekey in TypeFilters:
        config["components"]=[component
                              for component in components
                              if TypeFilters[typekey](component)]
        templates["%ss" % typekey]=init_template(config)

def add_master(config, templates):
    def filter_outputs(templates):        
        outputs={}
        for tempname, template in templates.items():
            outputs.update({paramname: tempname
                            for paramname in template["Outputs"]
                            if "Outputs" in template})
        return outputs
    def format_params(paramnames, outputs):
        """
        - global fn_getatt doesn't support 
          - pre- hungarorised names
          - template outputs syntax
        """
        def fn_getatt(name, attr):
            return {"Fn::GetAtt": [name, attr]}
        def stack_id(stackname):
            return "%s.Outputs" % logical_id("%s-stack" % stackname)
        """
        - NB pops internal outputs so they are not exported
        - will fail if two triggers want to bind to the same action
        """
        return {paramname: fn_getatt(stack_id(outputs.pop(paramname)),
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
    def init_template(config, templates):
        outputs=filter_outputs(templates)
        components=[init_stack(config, tempname, template, outputs)
                    for tempname, template in templates.items()]
        template=Template()
        for component in components:
            stack=synth_stack(**component)
            template.update(stack)
        template["outputs"]=format_params(outputs.keys(),
                                          outputs)
        return template.render()
    template=init_template(config, templates)
    templates["master"]=template
        
def synth_env(config):
    templates={}
    add_components(config, templates)
    add_master(config, templates)
    return templates

if __name__=="__main__":
    pass
