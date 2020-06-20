import os, sys, yaml

def KeyFn(component):
    return "%s/%s" % (component["type"],
                      component["name"])

def is_api(component):
    return component["type"]=="api"

def is_action(component):
    return component["type"]=="action"

def is_trigger(component):
    return not (is_api(component) or
                is_action(component))

def filter_actions(components):
    return [component
            for component in components
            if is_action(component)]

def remap_triggers(config):
    def validate_action(action, trigmap):
        trigkey=KeyFn(action["trigger"])
        if trigkey not in trigmap.keys():
            raise RuntimeError("trigger %s not found" % trigkey)
    def assert_unmapped(fn):
        def wrapped(action, trigger):
            if "action" in trigger:
                raise RuntimeError("trigger %s already mapped" % KeyFn(trigger))
            return fn(action, trigger)
        return wrapped
    @assert_unmapped
    def remap_queue(action, trigger):    
        trigaction={"name": action["name"]}
        trigger["action"]=trigaction
    @assert_unmapped
    def remap_table(action, trigger):    
        trigaction={"name": action["name"]}
        trigger["action"]=trigaction
    @assert_unmapped
    def remap_timer(action, trigger):    
        trigaction={"name": action["name"]}
        trigger["action"]=trigaction
    def remap_bucket(action, trigger):
        trigger.setdefault("actions", [])
        actionnames=[action["name"]
                     for action in trigger["actions"]]
        if action["name"] in actionnames:
            raise RuntimeError("%s already mapped" % KeyFn(trigger))
        trigaction={"name": action["name"],
                    "path": action["trigger"]["path"]}
        trigger["actions"].append(trigaction)
    trigmap={KeyFn(component):component
             for component in config["components"]
             if is_trigger(component)}
    for action in filter_actions(config["components"]):
        validate_action(action, trigmap)
        trigger=trigmap[KeyFn(action["trigger"])]
        remapfn=eval("remap_%s" % trigger["type"])
        remapfn(action=action,
                trigger=trigger)

def add_role_permissions(config):
    """
    - validate targets if they exist
    - infer permissions from targets
    - pass through custom permissions
    - add "lookback" permissions from `trigger`
    """
    pass
        
def preprocess(config):
    remap_triggers(config)
    add_role_permissions(config)
    for action in filter_actions(config["components"]):
        action.pop("trigger")
        
if __name__=="__main__":
    try:
        if len(sys.argv) < 2:
            raise RuntimeError("Please enter filename")
        filename=sys.argv[1]
        if not os.path.exists(filename):
            raise RuntimeError("File does not exist")
        if not filename.endswith(".yaml"):
            raise RuntimeError("File must be a yaml file")
        with open(filename, 'r') as f:
            config=yaml.load(f.read(),
                             Loader=yaml.FullLoader)
        preprocess(config)
        yaml.SafeDumper.ignore_aliases=lambda *args: True
        print (yaml.safe_dump(config,
                              default_flow_style=False))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
