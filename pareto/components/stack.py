from pareto.components import Parameter

from pareto.components.bucket import synth_bucket
from pareto.components.function import synth_function
from pareto.components.table import synth_table
from pareto.components.queue import synth_queue
from pareto.components.timer import synth_timer
from pareto.components.dashboard import synth_dashboard

def synth_stack(config):
    paramnames=[]
    def has_functions(config):
        for item in config["components"]:
            if item["type"]=="function":
                return True
        return False
    if has_functions(config):
        paramnames+=["s3-staging-bucket",
                     "s3-layer-key"]
    params=[Parameter(name=name)
            for name in paramnames]
    def add_component(component, stack):
        for attr in ["parameters",
                     "resources",
                     "outputs"]:
            if attr in component:
                stack.setdefault(attr, [])
                stack[attr]+=component[attr]
    stack={"parameters": params}    
    for item in config["components"]:
        item.update({k:config[k]
                     for k in config.keys()
                     if k!="components"})
        fn=eval("synth_%s" % item["type"])                
        component=fn(**item)
        add_component(component, stack)
    for attr in ["dashboard"]:
        fn=eval("synth_%s" % attr)
        config["name"]=attr
        component=fn(**config)
        add_component(component, stack)
    return {k.capitalize():dict(v)
            for k, v in stack.items()}

if __name__=="__main__":
    pass
