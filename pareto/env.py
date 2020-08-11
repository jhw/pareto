from pareto.components import *

from pareto.components.action import synth_action
from pareto.components.api import synth_api
from pareto.components.bucket import synth_bucket
from pareto.components.layer import synth_layer
from pareto.components.queue import synth_queue
from pareto.components.secret import synth_secret
from pareto.components.service import synth_service
from pareto.components.stack import synth_stack
from pareto.components.table import synth_table
from pareto.components.timer import synth_timer

from pareto.preprocessor import preprocess

from pareto.template import Template

import datetime, logging, os

Master="master"

"""
- services need to be separate from actions as action permissions to execute services assume service arns imported as parameters 
- layers need to be separate from actions else circular dependency error
"""

def TemplateMapper(groupkey,
                   dedicated=["layers",
                              "actions",
                              "services",
                              "apis"],
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

    """
    - include count state variable (dict)
    - include count in template key
    - bump count[tempkey] if metrics limit is breached
    """
    
    def check_metrics(fn):
        def wrapped(self, groupkey, component):
            tempkey=self.template_key(groupkey)
            template=self[tempkey].clone() if tempkey in self else Template()
            synthfn=eval("synth_%s" % groupkey[:-1])                
            synthfn(template, **component)
            # print ("%s -> %s" % (tempkey, template.metrics))
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

    def push(self, s3):
        def push(config, tempname, template, s3):
            key="%s-%s/templates/%s.json" % (config["globals"]["app"],
                                             config["globals"]["stage"],
                                             tempname)
            logging.info("pushing %s" % key)
            s3.put_object(Bucket=config["globals"]["bucket"],
                          Key=key,
                          Body=template.json_repr.encode("utf-8"),
                          ContentType='application/json')
        for tempname, template in self.items():
            if tempname==Master:
                continue
            push(self.config, tempname, template, s3)
    
    def deploy(self, cf):
        logging.info("deploying stack")
        def stack_exists(stackname):
            stacknames=[stack["StackName"]
                        for stack in cf.describe_stacks()["Stacks"]]
            return stackname in stacknames
        stackname="%s-%s" % (self.config["globals"]["app"],
                             self.config["globals"]["stage"])
        action="update" if stack_exists(stackname) else "create"
        fn=getattr(cf, "%s_stack" % action)
        fn(StackName=stackname,
           TemplateBody=self[Master].json_repr,
           Capabilities=["CAPABILITY_IAM"])
        waiter=cf.get_waiter("stack_%s_complete" % action)
        waiter.wait(StackName=stackname)

    def dump(self):
        logging.info("dumping templates")
        timestamp=datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
        for tempname, template in self.items():
            tokens=["tmp", "env", timestamp, "%s.yaml" % tempname]
            dirname, filename = "/".join(tokens[:-1]), "/".join(tokens)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            with open(filename, 'w') as f:
                f.write(template.yaml_repr)
        return self 

"""
- dump() executed before validate() for debugging
"""
    
@preprocess
def synth_env(config):
    return Env.create(config).validate().synth_master().dump()

if __name__=="__main__":
    pass
