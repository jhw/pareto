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
- `add_nested_templates` is super- opinionated about layouts
- bundles triggers, actions and related permissions/mappings under same nested templates so each can be indepedent / minimal parameter requiring required
- also makes use of template.dashboard which may be an over- optimisation
- but is not the only way to do it - could have triggers, actions and dashes in different stacks
- really all actions should export arns, just in case
- and triggers should be created with option of using parameter- based arns, in case you want to mess with the layout
- then could maybe experiment with different layouts at env level
"""

def add_nested_templates(config, templates):
    def template_name(config, key):
        return "%s-%s-%s" % (config["globals"]["app"],
                             key,
                             config["globals"]["stage"])
    def init_template(config, key, components):
        name=template_name(config, key)
        template=Template(name=name)
        for kwargs in components:
            kwargs.update(config["globals"]) # NB
            fn=eval("synth_%s" % key[:-1])                
            component=fn(**kwargs)
            template.update(component)
            if "action" in kwargs:
                template.update(synth_action(**kwargs))
        return template.render()
    for key, group in config["components"].items():
        name=template_name(config, key)
        templates[key]=init_template(config, key, group)

def add_master(config, templates):
    def init_stack(config, tempname):
        stack={"name": tempname}
        stack.update(config["globals"])
        return stack
    def init_template(config, templates):
        components=[init_stack(config, tempname)
                    for tempname in templates.keys()]
        template=Template()
        for kwargs in components:
            stack=synth_stack(**kwargs)
            template.update(stack)
        return template.render()
    templates["master"]=init_template(config, templates)
        
def synth_env(config):
    templates={}
    add_nested_templates(config, templates)
    add_master(config, templates)
    return templates

if __name__=="__main__":
    pass
