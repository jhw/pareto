from pareto.components import *

TypeFilters={
    "api": lambda x: x["type"]=="api",
    "action": lambda x: x["type"]=="action",
    "trigger": lambda x: x["type"] not in ["action", "api"]
    }

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

def KeyFn(component):
    return "%s/%s" % (component["type"],
                      component["name"])

def validate(**kwargs):
    def assert_unique(**kwargs):
        keys=[]
        for attr in kwargs.keys():
            keys+=[KeyFn(component)
                   for component in kwargs[attr]]
        ukeys=list(set(keys))
        if len(keys)!=len(ukeys):
            raise RuntimeError("keys are not unique")
    def assert_triggers(actions, triggers, **kwargs):
        def assert_refs(action, trigmap):
            for attr in ["trigger",
                         "target"]:
                trigkey=KeyFn(action[attr])
                if trigkey not in trigmap.keys():
                    raise RuntimeError("%s %s %s not found" % (KeyFn(action),
                                                               attr,
                                                               trigkey))
        trigmap={KeyFn(trigger):trigger
                 for trigger in triggers}
        for action in actions:
            assert_refs(action, trigmap)
    for fn in [assert_unique,
               assert_triggers]:
        fn(**kwargs)
            
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
        def wrapped(component):
            iam=fn(component)
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

def add_permissions(**kwargs):
    def func_permissions(component, attrs):
        def trigger_permissions(iam, trigger):
            trigconf=TriggerConfig[trigger["type"]]
            if trigconf["event_sourced"]:
                iam.add(trigconf["iam_name"])
        def target_permissions(iam, target):
            targconf=TriggerConfig[target["type"]]
            iam.add(targconf["iam_name"])
        iam=Iam.initialise(component)
        for attr in attrs:
            if attr in component:
                fn=eval("%s_permissions" % attr)
                fn(iam, component[attr])
        return iam        
    @Iam.attach
    def api_permissions(api):
        return func_permissions(component, ["target"])
    @Iam.attach
    def action_permissions(action):
        return func_permissions(component, ["trigger", "target"])
    @Iam.attach
    def trigger_permissions(trigger):
        pass
    for attr in kwargs.keys():
        for component in kwargs[attr]:
            fn=eval("%s_permissions" % (attr[:-1]))
            fn(component)

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
        for attr in ["trigger",
                     "target"]:
            action.pop(attr)
        
def preprocess(config, filters=TypeFilters):
    def apply_filter(components, filterfn):
        return [component
                for component in components
                if filterfn(component)]
    kwargs={"%ss" % attr: apply_filter(config["components"],
                                       filters[attr])
            for attr in filters.keys()}
    for fn in [validate,
               remap_triggers,
               add_permissions,
               remap_types,
               cleanup]:
        fn(**kwargs)
        
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
