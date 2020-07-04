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
        @assert_params
        def params_for_template(tempname, template, outputs):
            return {"foo": "bar"}
        outputs=filter_outputs(templates)
        config["components"]=[{"type": "stack",
                               "name": tempname,
                               "params": params_for_template(tempname,
                                                             template,
                                                             outputs)}
                              for tempname, template in templates.items()]
        templates["master"]=synth_template(config)
    templates={}
    add_components(config, templates)
    add_master(config, templates)
    return templates

if __name__=="__main__":
    pass
