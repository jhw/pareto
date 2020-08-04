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

def stack_param(paramname, outputs):
    return {"Fn::GetAtt": [outputs[paramname].capitalize(),
                           "Outputs.%s" % paramname]}

class Env(dict):

    @classmethod
    def create(self, config, templatefn=TemplateMapper):
        env=Env(config)
        for groupkey, components in config["components"].items():
            tempkey=templatefn(groupkey)
            env.setdefault(tempkey, Template())
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

    def stack_kwargs(self, tempkey, template):
        outputs=self.outputs
        kwargs={"name": tempkey,
                "params": {paramname: stack_param(paramname, outputs)
                           for paramname, _ in template.parameters}}
        kwargs.update(self.config["globals"])
        return kwargs

    def finalise(self):
        self["master"]=Template()
        for tempkey, template in self.items():
            kwargs=self.stack_kwargs(tempkey, template)
            stack=synth_stack(**kwargs)
            self["master"].update(stack)
        return self

    def render(self):
        return {k:v.render()
                for k, v in self.items()}

def synth_env(config):
    return Env.create(config).finalise().render();

if __name__=="__main__":
    pass
