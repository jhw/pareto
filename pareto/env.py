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
    def template_name(config, groupkey):
        return "%s-%s-%s" % (config["globals"]["app"],
                             groupkey,
                             config["globals"]["stage"])
    def init_template(config, groupkey, components):
        name=template_name(config, groupkey)
        template=Template(name=name)
        for kwargs in components:
            kwargs.update(config["globals"]) # NB
            fn=eval("synth_%s" % groupkey[:-1])                
            component=fn(**kwargs)
            template.update(component)            
        return template
    templates, outputs = {}, {}
    for groupkey, components in config["components"].items():
        template=init_template(config, groupkey, components)
        outputs.update({outputkey: groupkey
                        for outputkey, _ in template.outputs})
        templates[groupkey]=template.render()
    return templates, outputs

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
    return master.render()
        
def synth_env(config):
    templates, outputs = init_templates(config)
    templates["master"]=init_master(config, templates, outputs)    
    return templates

if __name__=="__main__":
    pass
