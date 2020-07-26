from pareto.components import *

from pareto.components.api import synth_api
from pareto.components.bucket import synth_bucket
from pareto.components.queue import synth_queue
from pareto.components.secret import synth_secret
from pareto.components.stack import synth_stack
from pareto.components.table import synth_table
from pareto.components.timer import synth_timer
from pareto.components.website import synth_website

def add_component_groups(config, templates):
    def init_component(config, component):
        component.update(config["globals"])
        return component
    def group_components(config):
        return {key: [init_component(config, component)
                      for component in components]
                for key, components in config["components"].items()}
    def init_template(key, components):
        template=Template(name="foobar")
        for kwargs in components:
            fn=eval("synth_%s" % key[:-1])                
            component=fn(**kwargs)
            template.update(component)
        return template.render()
    groups=group_components(config)
    for key, group in groups.items():
        templates[key]=init_template(key, group)

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
    for attr in ["component_groups",
                 "master"]:
        fn=eval("add_%s" % attr)
        fn(config, templates)
    return templates

if __name__=="__main__":
    pass
