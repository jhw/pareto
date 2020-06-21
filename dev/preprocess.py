import os, sys, yaml

def KeyFn(component):
    return "%s/%s" % (component["type"],
                      component["name"])

TypeFilters={
    "api": lambda x: x["type"]=="api",
    "action": lambda x: x["type"]=="action",
    "trigger": lambda x: x["type"] not in ["action", "api"]
    }

"""
- need to validate name uniqueness
- need to validate targets
"""

def cross_validate(actions, triggers, **kwargs):
    def validate_action(action, trigmap):
        trigkey=KeyFn(action["trigger"])
        if trigkey not in trigmap.keys():
            raise RuntimeError("trigger %s not found" % trigkey)
    trigmap={KeyFn(trigger):trigger
             for trigger in triggers}
    for action in actions:
        validate_action(action, trigmap)
    
"""
- DSL is action- centric; triggers are nested under actions, and reflect event type information
- but CF is trigger- centric; for non- event sourced triggers (s3, sns, cloudwatch event), action is explicitly nested under trigger as function reference
- pareto then uses same model for event sourced triggers (sqs, ddb, kinesis) for convenience, even though EventSourceMapping is an indepenent resource containing refs to both action and trigger
- remap_triggers therefore converts this action- centric model to a trigger- centric one used by underlying pareto components
"""
        
def remap_triggers(actions, triggers, **kwargs):
    def remap_bucket(action, trigger):
        trigger.setdefault("actions", [])
        actionnames=[action["name"]
                     for action in trigger["actions"]]
        if action["name"] in actionnames:
            raise RuntimeError("%s already mapped" % KeyFn(trigger))
        trigaction={"name": action["name"],
                    "path": action["trigger"]["path"]}
        trigger["actions"].append(trigaction)
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
    trigmap={KeyFn(trigger):trigger
             for trigger in triggers}
    for action in actions:
        trigger=trigmap[KeyFn(action["trigger"])]
        remapfn=eval("remap_%s" % trigger["type"])
        remapfn(action=action,
                trigger=trigger)

"""
- whole level of permissions needs adding
- any non- event sourced target (s3, sns, cloudwatch event) needs permission to call lambda
- but you don't have to worry about that, lambda permission is added by underlying pareto component
- action may need permissions to call target
- that target may a trigger (s3/sqs/ddb) or a non trigger (eg polly, translate)
- can infer trigger target permissions if target info is included at action level
- however needs to pass through non- trigger target permissions
- then a further problem with event source mappings (sqs, ddb, kinesis)
- although these are billed as event sourced, reality is that they poll their triggers
- hence they need "lookback" permissions to do that
"""
        
def add_permissions(actions, apis, **kwargs):
    for fn in actions+apis:
        if "permissions" in fn:
            fn["permissions"]={"iam": fn["permissions"]}

"""
- DSL follows zapier model of actions and triggers, and adds apis
- pareto components follow CF model more closely
- remap_types maps from former to latter
- trigger types don't need remapping as they are already defined as underlying pareto component type
"""

def remap_types(**kwargs):
    def remap_api(api):
        api["type"]="function"
        api["api"]={"method": api.pop("method")}
    def remap_action(action):        
        action["type"]="function"
    def remap_trigger(trigger):
        pass
    for attr in kwargs.keys():
        for component in kwargs[attr]:
            fn=eval("remap_%s" % (attr[:-1]))
            fn(component)

def cleanup(actions, **kwargs):
    for action in actions:
        action.pop("trigger")
        
def preprocess(config, filters=TypeFilters):
    def apply_filter(components, filterfn):
        return [component
                for component in components
                if filterfn(component)]
    kwargs={"%ss" % attr: apply_filter(config["components"],
                                       filters[attr])
            for attr in filters.keys()}
    for fn in [cross_validate,
               remap_triggers,
               add_permissions,
               remap_types,
               cleanup]:
        fn(**kwargs)
        
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
