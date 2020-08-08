from pareto.components import *

from pareto.components.action import synth_action
from pareto.components.api import synth_api
from pareto.components.bucket import synth_bucket
from pareto.components.queue import synth_queue
from pareto.components.secret import synth_secret
from pareto.components.stack import synth_stack
from pareto.components.table import synth_table
from pareto.components.timer import synth_timer

from pareto.preprocessor import preprocess

from pareto.template import Template

import datetime, logging, os

Master="master"

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
        def template_name(config, tempkey):
            return "%s-%s-%s" % (config["globals"]["app"],
                                 tempkey,
                                 config["globals"]["stage"])
        env=Env(config)
        for groupkey, components in config["components"].items():
            tempkey=templatefn(groupkey)
            tempname=template_name(config, tempkey)
            env.setdefault(tempkey, Template(name=tempname))
            for kwargs in components:
                kwargs.update(config["globals"]) # NB
                fn=eval("synth_%s" % groupkey[:-1])                
                fn(env[tempkey], **kwargs)
        return env
    
    def __init__(self, config, items={}):
        dict.__init__(self, items)
        self.config=config

    @property
    def outputs(self):
        outputs={}
        for tempkey, template in self.items():
            outputs.update({outputkey: tempkey
                            for outputkey in template.Outputs})
        return outputs

    def stack_kwargs(self, tempname, template, outputs):
        params={paramname: stack_param(paramname, outputs)
                for paramname in template.Parameters}
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

    @attach(Master)
    def synth_master(self):
        master=Template(name=Master)
        for tempname, template in self.items():
            kwargs=self.stack_kwargs(tempname, template, self.outputs)
            synth_stack(master, **kwargs)
        return master
    
    def validate(self):
        def validate_metrics(tempname, template):
            metrics=template.metrics
            for k, v in metrics.items():
                if v > 1:
                    raise RuntimeError("%s %s metrics exceeds limit" % (tempname, k))
        def validate_refs(tempname, template):
            resourceids=template.resource_ids
            for ref in template.resource_refs:
                if ref not in resourceids:
                    raise RuntimeError("bad reference to %s in %s template" % (ref, tempname))
        logging.info("validating templates")
        for tempname, template in self.items():
            validate_metrics(tempname, template)
            validate_refs(tempname, template)
        return self

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
    
@preprocess
def synth_env(config):
    return Env.create(config).synth_master().validate()

if __name__=="__main__":
    pass
