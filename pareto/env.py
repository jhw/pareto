from pareto.components import *

from pareto.components.action import synth_action
from pareto.components.api import synth_api
from pareto.components.bucket import synth_bucket
from pareto.components.dashboard import synth_dashboard
from pareto.components.queue import synth_queue
from pareto.components.secret import synth_secret
from pareto.components.stack import synth_stack
from pareto.components.table import synth_table
from pareto.components.timer import synth_timer
from pareto.components.website import synth_website

from pareto.preprocessor import preprocess

Actions, NonFunctionals = "actions", "non-functionals"

def TemplateMapper(groupkey,
                   dedicated=["actions",
                              "apis"],
                   default="misc"):
    return groupkey if groupkey in dedicated else default

def assert_output(fn):
    def wrapped(paramname, outputs):
        if paramname not in outputs:
            raise RuntimeError("%s not found in outputs" % paramname)
        return fn(paramname, outputs)
    return wrapped

@assert_output
def stack_param(paramname, outputs):    
    return {"Fn::GetAtt": [logical_id(outputs[paramname]),
                           "Outputs.%s" %  paramname]}

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

    def stack_kwargs(self, tempname, template, outputs):
        params={paramname: stack_param(paramname, outputs)
                for paramname, _ in template.parameters}
        stack={"name": tempname,
               "params": params}
        stack.update(self.config["globals"])
        return stack

    def attach(key):
        def decorator(fn):
            def wrapped(self):
                self[key]=fn(self)
                return self
            return wrapped
        return decorator

    @attach("dashboards")
    def synth_dash(self):
        def dash_name(config, tempkey):
            return "%s-%s-%s" % (config["globals"]["app"],
                                 tempkey,
                                 config["globals"]["stage"])
        dash=Template()
        for tempname, template in self.items():
            if template.charts==[]:
                continue
            name=dash_name(self.config, tempname)
            kwargs={"name": name,
                    "body": template.charts}
            stack=synth_dashboard(**kwargs)
            dash.update(stack)            
        return dash
    
    @attach("master")
    def synth_master(self):
        master=Template()
        for tempname, template in self.items():
            kwargs=self.stack_kwargs(tempname, template, self.outputs)
            stack=synth_stack(**kwargs)
            master.update(stack)
        return master

    def render(self):
        return {k:v.render()
                for k, v in self.items()}

@preprocess
def synth_env(config):
    return Env.create(config).synth_dash().synth_master().render()

if __name__=="__main__":
    pass
