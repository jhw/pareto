from pareto.components import *

TriggerConfig=yaml.load("""
bucket:
  iam_name: s3
  event_sourced: false
table:
  iam_name: dynamodb
  event_sourced: true
queue:
  iam_name: sqs
  event_sourced: true
""", Loader=yaml.FullLoader)

"""
- this is a temportary function which should wither away over time if actions ceases to be a dedicated class and instead all actions get nested under trigger classes
"""

def filter_triggers(components):
    triggers=[]
    for groupname, group in components.items():
        if groupname[:-1] in TriggerConfig:
            for component in group:
                component["type"]=groupname[:-1]
                triggers.append(component)
    return triggers

def validate(**components):
    def assert_unique(**components):
        keys=[]
        for attr in components:
            keys+=[component["name"]
                   for component in components[attr]]
        ukeys=list(set(keys))
        if len(keys)!=len(ukeys):
            raise RuntimeError("keys are not unique")
    def assert_triggers(**components):
        def assert_refs(action, trigmap):
            for attr in ["trigger",
                         "target"]:
                trigkey=action[attr]["name"]
                if trigkey not in trigmap:
                    raise RuntimeError("%s %s %s not found" % (action["name"],
                                                               attr,
                                                               trigkey))
        trigmap={trigger["name"]:trigger
                 for trigger in filter_triggers(components)}
        for action in components["actions"]:
            assert_refs(action, trigmap)
    for fn in [assert_unique,
               assert_triggers]:
        fn(**components)
            
"""
- DSL is action- centric; triggers are nested under actions, and reflect event type information
- but CF is trigger- centric; for non- event sourced triggers (s3, sns, cloudwatch event), action is explicitly nested under trigger as function reference
- pareto then uses same model for event sourced triggers (sqs, ddb, kinesis) for convenience, even though EventSourceMapping is an indepenent resource containing refs to both action and trigger
- remap_triggers therefore converts this action- centric model to a trigger- centric one used by underlying pareto components
"""
        
def remap_triggers(**components):
    def remap_bucket(action, trigger):
        trigger.setdefault("actions", [])
        actionnames=[action["name"]
                     for action in trigger["actions"]]
        if action["name"] in actionnames:
            raise RuntimeError("%s already mapped" % trigger["name"])
        trigaction={"name": action["name"],
                    "path": action["trigger"]["path"]}
        trigger["actions"].append(trigaction)
    def assert_unmapped(fn):
        def wrapped(action, trigger):
            if "action" in trigger:
                raise RuntimeError("trigger %s already mapped" % trigger["name"])
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
    trigmap={trigger["name"]:trigger
             for trigger in filter_triggers(components)}
    for action in components["actions"]:
        trigger=trigmap[action["trigger"]["name"]]
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

class Iam(list):

    @classmethod
    def initialise(self,
                   component,
                   defaults=["logs",
                             "sqs"]): # for dead letter queues
        permissions=component.pop("permissions") if "permissions" in component else []
        iam=Iam(permissions)
        for permission in defaults:
            iam.add(permission)
        return iam

    @classmethod
    def attach(self, fn):
        def wrapped(component, triggermap):
            iam=fn(component, triggermap)
            if (iam and
                not iam.is_empty):
                component["iam"]={"permissions": iam.render()}
        return wrapped

    def __init__(self, items):
        return list.__init__(self, items)

    def expand(fn):
        def wrapped(self, name):
            return fn(self, "%s:*" % name if ":" not in name else name)
        return wrapped

    @expand
    def add(self, permission):
        if permission not in self:
            self.append(permission)

    @property
    def is_empty(self):
        return len(self)==0

    def render(self):
        return list(self)

def add_permissions(**components):
    def func_permissions(component, triggermap, attrs):
        def trigger_permissions(trigger, triggertype, iam):
            trigconf=TriggerConfig[triggertype]
            if trigconf["event_sourced"]:
                iam.add(trigconf["iam_name"])
        def target_permissions(target, targettype, iam):
            targconf=TriggerConfig[targettype]
            iam.add(targconf["iam_name"])
        iam=Iam.initialise(component)
        for attr in attrs:
            if attr in component:
                fn=eval("%s_permissions" % attr)
                triggertype=triggermap[component[attr]["name"]]["type"]
                fn(component[attr], triggertype, iam)                    
        return iam        
    @Iam.attach
    def api_permissions(component, triggermap):
        return func_permissions(component,
                                triggermap,
                                ["target"])
    @Iam.attach
    def action_permissions(component, triggermap):
        return func_permissions(component,
                                triggermap,
                                ["trigger", "target"])
    triggermap={trigger["name"]:trigger
                for trigger in filter_triggers(components)}
    for attr in components:
        for component in components[attr]:
            if attr[:-1] not in TriggerConfig:
                fn=eval("%s_permissions" % (attr[:-1]))
                fn(component, triggermap)

"""
- DSL follows zapier model of actions and triggers, and adds apis
- pareto components follow CF model more closely
- remap_types maps from former to latter
- trigger types don't need remapping as they are already defined as underlying pareto component type
"""

def remap_types(**components):
    def remap_api(api):
        api["type"]="function"
        api["api"]={"method": api.pop("method")}
    def remap_action(action):        
        action["type"]="function"
    for attr in components:
        for component in components[attr]:
            if attr[:-1] not in TriggerConfig:
                fn=eval("remap_%s" % (attr[:-1]))
                fn(component)

def cleanup(actions, **components):
    for action in actions:
        for attr in ["trigger",
                     "target"]:
            action.pop(attr)

def preprocess(config):
    for fn in [validate,
               remap_triggers,
               add_permissions,
               remap_types,
               cleanup]:
        fn(**config["components"])
        
if __name__=="__main__":
    try:
        import os, sys
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
