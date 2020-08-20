from pareto.components import *

from pareto.components.action import synth_action
from pareto.components.api import synth_api
from pareto.components.bucket import synth_bucket
from pareto.components.layer import synth_layer
from pareto.components.queue import synth_queue
from pareto.components.secret import synth_secret
from pareto.components.stack import synth_stack
from pareto.components.table import synth_table
from pareto.components.timer import synth_timer
from pareto.components.userpool import synth_userpool

from pareto.preprocessor import preprocess

from pareto.template import Template

import datetime, logging, os

Master="master"

def TemplateMapper(groupkey,
                   dedicated=["layers",
                              "actions",
                              "apis",
                              "userpools"],
                   default="misc"):
    return groupkey if groupkey in dedicated else default

class Refs(list):

    @classmethod
    def filter_params(self, env):
        return self.create(env, "Parameters")

    @classmethod
    def filter_outputs(self, env):
        return self.create(env, "Outputs")

    @classmethod
    def create(self, env, attr):
        refs=Refs()
        for tempname, template in env.items():
            refs+=[(key, tempname)                   
                   for key in getattr(template, attr)]
        return refs

    def __init__(self):
        list.__init__(self)

    def cross_validate(self, refs):
        attrs, errors = dict(self), []
        for attr, tempname in refs:
            if attr not in attrs:
                errors.append("%s not found" % attr)
            elif attrs[attr]==tempname:
                errors.append("%s can't be both parameter and output in same template")
        if errors!=[]:
            raise RuntimeError(", ".join(errors))

    def output_parameters(self, attrs):
        refs=dict(self)
        return {attr: {"Fn::GetAtt": [logical_id(refs[attr]),
                                      "Outputs.%s" %  attr]}
                for attr in attrs}
            
class Env(dict):

    @classmethod
    def create(self, config):
        env=Env(config)
        for groupkey, components in config["components"].items():
            for component in components:
                component.update(env.config["globals"]) # NB
                env.add_component(groupkey, component)
        return env
    
    def __init__(self, config, items={}):
        dict.__init__(self, items)
        self.config=config
        self.count={}

    def init_count(fn):
        def wrapped(self, groupkey, **kwargs):
            self.count.setdefault(groupkey, 1)
            return fn(self, groupkey, **kwargs)
        return wrapped
        
    @init_count
    def template_key(self, groupkey, templatefn=TemplateMapper):
        return "%s-%i" % (templatefn(groupkey),
                         self.count[groupkey])
        
    def template_name(self, tempkey):
        return "%s-%s-%s" % (self.config["globals"]["app"],
                             tempkey,
                             self.config["globals"]["stage"])

    def check_metrics(fn):
        def is_valid(template):
            # print (template.metrics)
            return max(template.metrics.values()) < 1
        def wrapped(self, groupkey, component):
            tempkey=self.template_key(groupkey)
            template=self[tempkey].clone() if tempkey in self else Template()
            synthfn=eval("synth_%s" % groupkey[:-1])                
            synthfn(template, **component)
            if not is_valid(template):
                self.count[groupkey]+=1
            return fn(self, groupkey, component)
        return wrapped
    
    def init_template(fn):
        def wrapped(self, groupkey, component):
            tempkey=self.template_key(groupkey)
            if tempkey not in self:
                tempname=self.template_name(tempkey)
                self[tempkey]=Template(name=tempname)
            return fn(self, groupkey, component)
        return wrapped

    @check_metrics
    @init_template
    def add_component(self, groupkey, component):
        tempkey=self.template_key(groupkey)
        template=self[tempkey]
        synthfn=eval("synth_%s" % groupkey[:-1])                
        synthfn(template, **component)
    
    def validate(self):
        def validate_outer(self):
            outputs=Refs.filter_outputs(self)
            params=Refs.filter_params(self)
            outputs.cross_validate(params)
        def validate_inner(self):
            for tempname, template in self.items():
                resourceids=template.resource_ids
                for ref in template.resource_refs:
                    if ref not in resourceids:
                        raise RuntimeError("bad reference to %s in %s template" % (ref, tempname))
        validate_outer(self)
        validate_inner(self)
        return self
        
    def attach(key):
        def decorator(fn):
            def wrapped(self):
                resp=fn(self)
                if resp:
                    self[key]=resp
                return self
            return wrapped
        return decorator

    @attach(Master)
    def synth_master(self):
        master=Template(name=Master)
        outputs=Refs.filter_outputs(self)
        for tempname, template in self.items():
            paramnames=list(template.Parameters.keys())
            params=outputs.output_parameters(paramnames)
            kwargs={"name": tempname,
                    "params": params}
            kwargs.update(self.config["globals"])
            synth_stack(master, **kwargs)
        return master

    def dump_yaml(self, timestamp):
        for tempname, template in self.items():
            tokens=["tmp", "env", timestamp, "yaml", "%s.yaml" % tempname]
            dirname, filename = "/".join(tokens[:-1]), "/".join(tokens)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            with open(filename, 'w') as f:
                f.write(template.yaml_repr)
        return self

    def dump_json(self, timestamp):
        for tempname, template in self.items():
            tokens=["tmp", "env", timestamp, "json", "%s.json" % tempname]
            dirname, filename = "/".join(tokens[:-1]), "/".join(tokens)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            with open(filename, 'w') as f:
                f.write(template.json_repr)
        return self 

    def dump(self, timestamp):
        return self.dump_yaml(timestamp).dump_json(timestamp)
    
"""
- first dumping to get output prior to validation, second to get any post- validation changes (master, dashboards)
"""
    
@preprocess
def synth_env(config):
    ts=datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
    return Env.create(config).dump(ts).validate().synth_master().dump(ts)

if __name__=="__main__":
    pass
