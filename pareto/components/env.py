from pareto.components import *

from pareto.components.api import synth_api
from pareto.components.bucket import synth_bucket, synth_website
from pareto.components.dashboard import synth_dashboard
from pareto.components.queue import synth_queue
from pareto.components.stack import synth_stack
from pareto.components.table import synth_table
from pareto.components.timer import synth_timer

def add_component_groups(config, templates):
    def init_component(config, component):
        component.update(config["globals"])
        return component
    def group_components(config):
        return {key: [init_component(config, component)
                      for component in components]
                for key, components in config["components"].items()}
    def init_template(key, components):
        template=Template()
        for kwargs in components:
            fn=eval("synth_%s" % key[:-1])                
            component=fn(**kwargs)
            template.update(component)
        return template.render()
    groups=group_components(config)
    for key, group in groups.items():
        templates[key]=init_template(key, group)

def add_dashboards(config, templates):
    def init_group(config, components):
        group=dict(config["globals"])
        group["components"]=components
        return group
    def has_dashboard(components):
        for component in components:
            if "action" in component:
                return True
        return False
    def init_groups(config):
        groups={}
        for key, components in config["components"].items():
            if not has_dashboard(components):
                continue
            group=init_group(config, components)
            groups[key]=group
        return groups
    groups=init_groups(config)
    template=Template()    
    for key, kwargs in groups.items():
        kwargs["name"]="%s-dashboard" % key
        dashboard=synth_dashboard(**kwargs)
        template.update(dashboard)
    templates["dashboards"]=template.render()

def add_master(config, templates):
    def init_stack(config, tempname):
        stack={"name": tempname}
        stack.update(config["globals"])
        return stack
    def add_secrets(config, template):
        @resource(suffix="secret")
        def Secret(**kwargs):
            secret=kwargs["value"] if type(kwargs["value"])==str else json.dumps(kwargs["value"])
            props={"Name": kwargs["name"],
                   "SecretString": secret}
            return "AWS::SecretsManager::Secret", props        
        template["resources"]+=[Secret(**secret)
                                for secret in config["secrets"]]
    def init_template(config, templates):
        components=[init_stack(config, tempname)
                    for tempname in templates.keys()]
        template=Template()
        for kwargs in components:
            stack=synth_stack(**kwargs)
            template.update(stack)
        if "secrets" in config:
            add_secrets(config, template)
        return template.render()
    templates["master"]=init_template(config, templates)
        
def synth_env(config):
    templates={}
    for attr in ["component_groups",
                 "dashboards",
                 "master"]:
        fn=eval("add_%s" % attr)
        fn(config, templates)
    return templates

if __name__=="__main__":
    pass
