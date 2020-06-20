import os, sys, yaml

"""
- components are either functional or non- functional
- functional components are either event handler or api
- different forms of event binding
  - direct invocation plus invocation permission (s3/sns/cloudwatch event)
  - event source mapping (sqs, ddb, kinesis)
- lambda permissions and event source mapping are included as separate resources whenever you initialise a non- functional component using `pareto.components`
- this leaves two role for the preprocessor
  - adding function IAM roles
  - defining non- functional targets
    - because dsl uses multidirectional src/dest attributes, whilst underlying components use unidirectional target (dest) attributes
- (a multidirectional dsl is useful for skeleton generator to define service stubs )
- function IAM roles are also bi- directional
  - function may need permission to invoke a target non- functional
  - event source mapping actually involves polling, so if you are using ddb or sqs in an event source map then function also needs "lookback" permissions :-/
"""

TriggerTypes=yaml.load("""
- bucket
- queue
- table
- timer
""", Loader=yaml.FullLoader)

def preprocess(config):
    def keyfn(component):
        return "%s/%s" % (component["type"],
                          component["name"])
    def is_trigger(component, types=TriggerTypes):
        return component["type"] in types
    def is_action(component):
        return (component["type"]=="function" and
                "api" not in component)
    def filter_actions(components):
        return [component
                for component in components
                if is_action(component)]
    def validate_action(func, triggermap):
        triggerkeys=triggermap.keys()
        for attr in ["trigger"]:
            triggerkey=keyfn(func[attr])
            if triggerkey not in triggerkeys:
                raise RuntimeError("%s not found" % triggerkey)
    def add_bucket_action(self, func, binding):
        self.setdefault("actions", [])
        actionnames=[action["name"]
                     for action in self["actions"]]
        if func["name"] in actionnames:
            raise RuntimeError("%s already mapped" % keyfn(self))
        action={"name": func["name"],
                "path": binding["path"]}
        self["actions"].append(action)
    def add_queue_action(self, func, binding):    
        if "action" in self:
            raise RuntimeError("%s already mapped" % keyfn(self))
        action={"name": func["name"]}
        if "batch" in binding:
            action["batch"]=binding["batch"]
        self["action"]=action
    def add_table_action(self, func, binding):    
        if "action" in self:
            raise RuntimeError("%s already mapped" % keyfn(self))
        action={"name": func["name"]}
        self["action"]=action
    def add_timer_action(self, func, binding):    
        if "action" in self:
            raise RuntimeError("%s already mapped" % keyfn(self))
        action={"name": func["name"]}
        self["action"]=action
    triggermap={keyfn(component):component
                for component in config["components"]
                if is_trigger(component)}    
    for func in filter_actions(config["components"]):
        validate_action(func, triggermap)
        binding=func.pop("trigger")
        trigger=triggermap[keyfn(binding)]
        actionfn=eval("add_%s_action" % trigger["type"])
        actionfn(self=trigger,                 
                 func=func,
                 binding=binding)
        
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
