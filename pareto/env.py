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

class Templates(dict):

    def __init__(self, items={}):
        dict.__init__(self, items)

    @property
    def outputs(self):
        outputs={}
        for tempkey, template in self.items():
            outputs.update({outputkey: tempkey
                            for outputkey, _ in template.outputs})
        return outputs

def TemplateMapper(groupkey):
    # return "actions" if groupkey=="actions" else "triggers"
    return groupkey
    
def init_templates(config, templatefn=TemplateMapper):
    def init_template(config, groupkey, components):
        template=Template()
        for kwargs in components:
            kwargs.update(config["globals"]) # NB
            fn=eval("synth_%s" % groupkey[:-1])                
            component=fn(**kwargs)
            template.update(component)            
        return template
    templates=Templates()
    for groupkey, components in config["components"].items():
        tempkey=templatefn(groupkey)
        templates[tempkey]=init_template(config, groupkey, components)
    return templates

def init_master(config, templates):
    def nested_param(outputs, paramname):
        return {"Fn::GetAtt": [outputs[paramname].capitalize(),
                               "Outputs.%s" %  paramname]}
    def init_stack(config, tempname, template, outputs):
        stack={"name": tempname}
        stack.update(config["globals"])
        stack["params"]={paramname: nested_param(outputs, paramname)
                         for paramname, _ in template.parameters}
        return stack
    master=Template()
    for tempname, template in templates.items():
        kwargs=init_stack(config, tempname, template, templates.outputs)
        stack=synth_stack(**kwargs)
        master.update(stack)
    return master

def render(fn):
    def wrapped(config):
        return {k:v.render()
                for k, v in fn(config).items()}
    return wrapped

@render
def synth_env(config):
    templates=init_templates(config)
    templates["master"]=init_master(config, templates)
    return templates

if __name__=="__main__":
    pass
