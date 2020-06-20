import os, sys, yaml

"""
- inspired by zapier twitter/lambda integration nomenclature
- triggers, actions, apis
"""

def preprocess(config):
    def keyfn(component):
        return "%s/%s" % (component["type"],
                          component["name"])
    def is_action(component):
        return component["type"]=="action"
    def is_api(component):
        return component["type"]=="api"
    def is_trigger(component):
        return not (is_action(component) or
                    is_api(component))
    def filter_actions(components):
        return [component
                for component in components
                if is_action(component)]
    def validate_action(action, trigmap):
        trigkey=keyfn(action["trigger"])
        if trigkey not in trigmap.keys():
            raise RuntimeError("trigger %s not found" % trigkey)
    def add_bucket_action(trigger, action):
        trigger.setdefault("actions", [])
        actionnames=[action["name"]
                     for action in trigger["actions"]]
        if action["name"] in actionnames:
            raise RuntimeError("%s already mapped" % keyfn(trigger))
        trigaction={"name": action["name"],
                    "path": action["trigger"]["path"]}
        trigger["actions"].append(trigaction)
    def trigger_unmapped(fn):
        def wrapped(trigger, action):
            if "action" in trigger:
                raise RuntimeError("trigger %s already mapped" % keyfn(trigger))
            return fn(trigger, action)
        return wrapped
    @trigger_unmapped
    def add_queue_action(trigger, action):    
        trigaction={"name": action["name"]}
        trigger["action"]=trigaction
    @trigger_unmapped
    def add_table_action(trigger, action):    
        trigaction={"name": action["name"]}
        trigger["action"]=trigaction
    @trigger_unmapped
    def add_timer_action(trigger, action):    
        trigaction={"name": action["name"]}
        trigger["action"]=trigaction
    trigmap={keyfn(component):component
             for component in config["components"]
             if is_trigger(component)}
    for action in filter_actions(config["components"]):
        validate_action(action, trigmap)
        trigger=trigmap[keyfn(action["trigger"])]
        actionfn=eval("add_%s_action" % trigger["type"])
        actionfn(action=action,
                 trigger=trigger)
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
