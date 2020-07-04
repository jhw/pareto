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
    def filter_outputs(templates):
        outputs={}
        for tempname, template in templates.items():
            outputs.update({paramname: tempname
                            for paramname in template["Outputs"]
                            if "Outputs" in template})
        return outputs
    def assert_params(fn):
        def wrapped(tempname, template, outputs):
            return {} if "Parameters" not in template else fn(tempname,
                                                              template,
                                                              outputs)
        return wrapped
    def parent_output_id(paramname, outputs):
        stackname=logical_id("%s-stack" % outputs[paramname])
        return "%s.Outputs" % stackname
    """
    - local version of fn_getatt since global version doesn't support template outputs syntax, nor pre- hungarorised names
    """
    def fn_getatt(name, attr):
        return {"Fn::GetAtt": [name, attr]}
    @assert_params
    def params_for_template(tempname, template, outputs):
        return {paramname: fn_getatt(parent_output_id(paramname,
                                                      outputs),
                                     paramname)
                for paramname in list(template["Parameters"].keys())}
    outputs=filter_outputs(templates)
    config["components"]=[{"type": "stack",
                           "name": tempname,
                           "params": params_for_template(tempname,
                                                         template,
                                                         outputs)}
                          for tempname, template in templates.items()]
    templates["master"]=synth_template(config)
        
def synth_env(config):
    templates={}
    add_components(config, templates)
    add_master(config, templates)
    return templates

if __name__=="__main__":
    pass
