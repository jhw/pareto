from pareto.components import *

TriggerConfig=yaml.load("""
bucket:
  iam_name: s3
  event_sourced: false
website:
  iam_name: s3
  event_sourced: false
table:
  iam_name: dynamodb
  event_sourced: true
queue:
  iam_name: sqs
  event_sourced: true
""", Loader=yaml.FullLoader)

def add_types(functypes=["apis", "actions"], **components):
    for attr in components:
        for component in components[attr]:
            component["type"]=attr[:-1]
            component["functional"]=attr in functypes

"""
- this is a temportary function which should wither away over time if actions ceases to be a dedicated class and instead all actions get nested under trigger classes
"""

def filter_triggers(components):
    triggers=[]
    for groupname, group in components.items():
        if groupname[:-1] in TriggerConfig:
            for component in group:
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
            for attr in ["trigger"]:
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

def cleanup(actions, **components):
    for action in actions:
        for attr in ["trigger"]:
            action.pop(attr)

def preprocess(config):
    for fn in [add_types,
               validate,
               remap_triggers,
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
