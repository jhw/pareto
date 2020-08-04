from pareto.components import *

from pareto.components.action import synth_action
from pareto.components.api import synth_api
from pareto.components.bucket import synth_bucket
from pareto.components.queue import synth_queue
from pareto.components.secret import synth_secret
from pareto.components.stack import synth_stack
from pareto.components.table import synth_table
from pareto.components.timer import synth_timer
from pareto.components.website import synth_website

def init_templates(config):
    def init_template(config, tempkey, components):
        template=Template()
        for kwargs in components:
            kwargs.update(config["globals"]) # NB
            fn=eval("synth_%s" % tempkey[:-1])                
            component=fn(**kwargs)
            template.update(component)            
        return template
    return {tempkey: init_template(config, tempkey, components)
            for tempkey, components in config["components"].items()}

def filter_outputs(templates):
    outputs={}
    for tempkey, template in templates.items():
        outputs.update({outputkey: tempkey
                        for outputkey, _ in template.outputs})
    return outputs
        
def init_master(config, templates, outputs):
    def nested_param(outputs, paramname):
        return {"Fn::GetAtt": [outputs[paramname].capitalize(),
                               "Outputs.%s" %  paramname]}
    def init_stack(config, tempname, template, outputs):
        stack={"name": tempname}
        stack.update(config["globals"])
        if "Parameters" in template:
            stack["params"]={paramname: nested_param(outputs, paramname)
                             for paramname in template["Parameters"]}
        return stack
    master=Template()
    for tempname, template in templates.items():
        kwargs=init_stack(config, tempname, template, outputs)
        stack=synth_stack(**kwargs)
        master.update(stack)
    return master
        
def synth_env(config):
    templates=init_templates(config)
    outputs=filter_outputs(templates)
    for tempkey, template in templates.items():
        templates[tempkey]=template.render()
    templates["master"]=init_master(config, templates, outputs).render()
    return templates

if __name__=="__main__":
    pass
