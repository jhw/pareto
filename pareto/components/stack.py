from pareto.components.bucket import synth_bucket
from pareto.components.function import synth_function
from pareto.components.table import synth_table
from pareto.components.queue import synth_queue
from pareto.components.timer import synth_timer
from pareto.components.dashboard import synth_dashboard

def synth_stack(config):
    def add_component(component, stack):
        for attr in ["resources",
                     "outputs"]:
            if attr in component:
                stack.setdefault(attr, [])
                stack[attr]+=component[attr]
    stack={}    
    for item in config["components"]:
        item.update({k:config[k]
                     for k in config.keys()
                     if k!="components"})
        fn=eval("synth_%s" % item["type"])                
        component=fn(**item)
        add_component(component, stack)
    def has_dashboard(config):
        functions=[component
                   for component in config["components"]
                   if component["type"]=="function"]
        return len(functions) > 0
    for attr in ["dashboard"]:
        fn=eval("has_%s" % attr)
        if not fn(config):
            continue
        fn=eval("synth_%s" % attr)
        config["name"]=attr
        component=fn(**config)
        add_component(component, stack)
    return {k.capitalize():dict(v)
            for k, v in stack.items()
            if len(v) > 0}

if __name__=="__main__":
    pass
