from pareto.components import *

from pareto.components.action import synth_action
from pareto.components.api import synth_api
from pareto.components.bucket import synth_bucket
from pareto.components.layer import synth_layer
from pareto.components.preprocessor import preprocess
from pareto.components.queue import synth_queue
from pareto.components.secret import synth_secret
from pareto.components.stack import synth_stack
from pareto.components.table import synth_table
from pareto.components.template import Template
from pareto.components.timer import synth_timer
from pareto.components.userpool import synth_userpool

import datetime, logging, os, zipfile

Master="master"

def TemplateMapper(groupkey,
                   dedicated=["layers",
                              "actions",
                              "apis",
                              "userpools"],
                   default="misc"):
    return groupkey if groupkey in dedicated else default

class Outputs(list):

    @classmethod
    def create(self, env, attr="Outputs"):
        outputs=Outputs()
        for template in env.values():
            outputs+=[(key, template.name)                   
                     for key in getattr(template, attr)]
        return outputs
    
    def __init__(self):
        list.__init__(self)

    def exported_attrs(self, template):
        refs=dict(self)
        return {attr: {"Fn::GetAtt": [logical_id(refs[attr]),
                                      "Outputs.%s" %  attr]}
                for attr in template.Parameters
                if attr in refs}
    
    def unlocated_refs(self, template):
        refs=dict(self)
        return {attr: {"Ref": attr}
                for attr in template.Parameters
                if attr not in refs}

    def unlocated_params(self, template):
        refs=dict(self)
        return {attr: {"Type": "String"}
                for attr in template.Parameters
                if attr not in refs}

    def stack_params(self, template):
        params={}
        params.update(self.exported_attrs(template))
        params.update(self.unlocated_refs(template))
        return params
    
class Env(dict):

    @classmethod
    def create(self, config):
        env=Env(config)
        for groupkey, components in config["components"].items():
            for component in components:
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
        
    def check_metrics(fn):
        def is_valid(template):
            return max(template.metrics.values()) < 1
        def wrapped(self, groupkey, component):
            tempkey=self.template_key(groupkey)
            clonename=random_id("cloned-template")
            template=self[tempkey].clone(clonename) if tempkey in self else Template(clonename)
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
                self[tempkey]=Template(name=tempkey)
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
        for template in self.values():
            template.validate()
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

    def expand(self):
        env=Env(self.config)
        for parent in self.values():
            for template in parent.expand():
                env[template.name]=template
        return env
            
    def master_params(fn):
        def listify(fn):
            def wrapped(self):
                return [(k, v)
                        for k, v in fn(self).items()]
            return wrapped
        @listify
        def filter_params(self):
            outputs, params = Outputs.create(self), {}
            for template in self.values():
                params.update(outputs.unlocated_params(template))
            return params
        def wrapped(self):
            master=fn(self)
            master.update(Parameters=filter_params(self))
            return master
        return wrapped

    @attach(Master)
    @master_params
    def synth_master(self):
        master=Template(name=Master)
        outputs=Outputs.create(self)
        for template in self.values():
            stackparams=outputs.stack_params(template)
            kwargs={"name": template.name,
                    "params": stackparams}
            synth_stack(master, **kwargs)
        return master

    def assert_root(fn):
        def wrapped(self, root):
            if not os.path.exists(root):
                os.makedirs(root)
            return fn(self, root)
        return wrapped
    
    @assert_root
    def dump(self, root):
        ts=datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
        zfname="%s/%s.zip" % (root, ts)
        logging.info("dumping to %s" % zfname)
        zf=zipfile.ZipFile(zfname, 'w', zipfile.ZIP_DEFLATED)
        for template in self.values():
            for attr in ["json", "yaml"]:
                filename="%s.%s" % (template.name, attr)
                prop=getattr(template, "%s_repr" % attr)
                zf.writestr(filename, prop)
        zf.close()
        return self
    
@preprocess
def synth_env(config):
    return Env.create(config).expand().synth_master().dump("tmp/templates").validate()

if __name__=="__main__":
    pass
