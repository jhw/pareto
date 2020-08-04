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

"""
- `init_templates` is super- opinionated about layouts
- bundles triggers, actions and related permissions/mappings under same nested templates so each can be indepedent / minimal parameter requiring required
- also makes use of template.dashboard which may be an over- optimisation
- but is not the only way to do it - could have triggers, actions and dashes in different stacks
- really all actions should export arns, just in case
- and triggers should be created with option of using parameter- based arns, in case you want to mess with the layout
- then could maybe experiment with different layouts at env level
"""

def init_templates(config, templates, outputs):
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
        return template.render()
    for groupkey, components in config["components"].items():
        name=template_name(config, groupkey)
        template=init_template(config, groupkey, components)
        if "Outputs" in template:
            outputs.update({outputkey: groupkey.capitalize() 
                            for outputkey in template["Outputs"]})
        templates[groupkey]=template

def init_master(config, templates, outputs):
    def init_stack(config, tempname, template, outputs):
        stack={"name": tempname}
        stack.update(config["globals"])
        if "Parameters" in template:
            stack["params"]={paramname: fn_getatt("foobar", # outputs[paramname]
                                                  paramname)
                             for paramname in template["Parameters"]}
        return stack
    def init_master(config, templates):
        master=Template()
        for tempname, template in templates.items():
            kwargs=init_stack(config, tempname, template, outputs)
            stack=synth_stack(**kwargs)
            master.update(stack)
        return master.render()
    templates["master"]=init_master(config, templates)
        
def synth_env(config):
    templates, outputs = {}, {}
    init_templates(config, templates, outputs)
    init_master(config, templates, outputs)
    return templates

if __name__=="__main__":
    pass
