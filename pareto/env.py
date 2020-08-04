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

Actions, Triggers = "actions", "triggers"

def TemplateMapper(groupkey):
    return Actions if groupkey==Actions else Triggers

class Env(dict):

    @classmethod
    def create(self, config, templatefn=TemplateMapper):
        env=Env()
        for groupkey, components in config["components"].items():
            tempkey=templatefn(groupkey)
            env.setdefault(tempkey, Template())
            for kwargs in components:
                kwargs.update(config["globals"]) # NB
                fn=eval("synth_%s" % groupkey[:-1])                
                component=fn(**kwargs)
                env[tempkey].update(component)         
        return env
    
    def __init__(self, items={}):
        dict.__init__(self, items)

    @property
    def outputs(self):
        outputs={}
        for tempkey, template in self.items():
            outputs.update({outputkey: tempkey
                            for outputkey, _ in template.outputs})
        return outputs

def init_master(config, env):
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
    for tempname, template in env.items():
        kwargs=init_stack(config, tempname, template, env.outputs)
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
    env=Env.create(config)
    env["master"]=init_master(config, env)
    return env

if __name__=="__main__":
    pass
