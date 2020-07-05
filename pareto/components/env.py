from pareto.components import *

from pareto.components.template import synth_template

TypeFilters={
    "api": lambda x: x["type"]=="function" and "api" in x,
    "action": lambda x: x["type"]=="function" and "api" not in x,
    "trigger": lambda x: x["type"]!="function"
    }

def add_components(config, templates):
    components=config.pop("components")
    for typekey in TypeFilters:
        config["components"]=[component
                              for component in components
                              if TypeFilters[typekey](component)]
        templates["%ss" % typekey]=synth_template(config)

def add_master(config, templates):
    def nested_outputs(templates):        
        outputs={}
        for tempname, template in templates.items():
            outputs.update({paramname: tempname
                            for paramname in template["Outputs"]
                            if "Outputs" in template})
        return outputs
    def init_params(paramnames, outputs):
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
    def nested_params(template, outputs):
        return init_params(template["Parameters"].keys(),
                           outputs) if "Parameters" in template else {}
    outputs=nested_outputs(templates)
    config["components"]=[{"type": "stack",
                           "name": tempname,
                           "params": nested_params(template,
                                                   outputs)}
                          for tempname, template in templates.items()]
    template=synth_template(config)
    template["Outputs"]=init_params(outputs.keys(),
                                    outputs)
    templates["master"]=template
        
def synth_env(config):
    templates={}
    add_components(config, templates)
    add_master(config, templates)
    return templates

if __name__=="__main__":
    pass
