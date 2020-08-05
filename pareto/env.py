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

Actions, NonFunctionals = "actions", "non-functionals"

LookbackPermissions=yaml.safe_load("""
table:
- dynamodb:DescribeStream
- dynamodb:GetRecords
- dynamodb:GetShardIterator
- dynamodb:ListStreams
queue:
- sqs:DeleteMessage
- sqs:GetQueueAttributes
- sqs:ReceiveMessage
""")

def TemplateMapper(groupkey):
    return Actions if groupkey==Actions else NonFunctionals

def stack_param(paramname, outputs):
    return {"Fn::GetAtt": [logical_id(outputs[paramname]),
                           "Outputs.%s" %  paramname]}

def validate(config):
    def filter_names(config):
        names=[]
        for groupkey in config["components"]:
            for component in config["components"][groupkey]:
                names.append(component["name"])
        return names
    def filter_action_refs(config):
        names=[]
        for groupkey in config["components"]:
            for component in config["components"][groupkey]:
                if "action" in component:
                    names.append(component["action"])
        return names
    def validate_unique_names(config):
        names=filter_names(config)
        unames=list(set(names))
        if len(names)!=len(unames):
            raise RuntimeError("component names are not unique")
    def validate_action_refs(config):
        names=filter_names(config)
        for ref in filter_action_refs(config):
            if ref not in names:
                raise RuntimeError("ref %s not found in component names" % ref)
    validate_unique_names(config)
    validate_action_refs(config)

def assert_actions(fn):
    def wrapped(config):
        if "actions" in config["components"]:
            return fn(config)
    return wrapped
    
@assert_actions
def preprocessor(config):
    def filter_actions(config):
        return {action["name"]:action
                for action in config["components"]["actions"]}
    def filter_types(config):
        types={}
        for groupkey in config["components"]:
            for component in config["components"][groupkey]:
                if "action" in component:
                    types[component["action"]]=groupkey[:-1]
        return types
    actions, types = filter_actions(config), filter_types(config)
    for actionname, action in actions.items():
        if (actionname in types and
            types[actionname] in LookbackPermissions):
            action.setdefault("permissions", [])
            action["permissions"]+=LookbackPermissions[types[actionname]]
    
class Env(dict):

    @classmethod
    def create(self, config, templatefn=TemplateMapper):
        env=Env(config)
        for groupkey, components in config["components"].items():
            tempkey=templatefn(groupkey)
            env.setdefault(tempkey, Template(name="hello-world"))
            for kwargs in components:
                kwargs.update(config["globals"]) # NB
                fn=eval("synth_%s" % groupkey[:-1])                
                component=fn(**kwargs)
                env[tempkey].update(component)         
        return env
    
    def __init__(self, config, items={}):
        dict.__init__(self, items)
        self.config=config

    @property
    def outputs(self):
        outputs={}
        for tempkey, template in self.items():
            outputs.update({outputkey: tempkey
                            for outputkey, _ in template.outputs})
        return outputs

    def stack_kwargs(self, tempname, template, outputs):
        params={paramname: stack_param(paramname, outputs)
                for paramname, _ in template.parameters}
        stack={"name": tempname,
               "params": params}
        stack.update(self.config["globals"])
        return stack

    def finalise(self):
        master=Template(name="master")
        for tempname, template in self.items():
            kwargs=self.stack_kwargs(tempname, template, self.outputs)
            stack=synth_stack(**kwargs)
            master.update(stack)
        self["master"]=master # NB append at end so not iterated over
        return self

    def render(self):
        return {k:v.render()
                for k, v in self.items()}

def prevalidate(fn):
    def wrapped(config):
        validate(config)
        return fn(config)
    return wrapped

def preprocess(fn):
    def wrapped(config):
        preprocessor(config)
        return fn(config)
    return wrapped
    
@prevalidate
@preprocess
def synth_env(config):
    return Env.create(config).finalise().render()

if __name__=="__main__":
    pass
