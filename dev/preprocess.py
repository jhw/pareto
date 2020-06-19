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

NonFunctionalTypes=yaml.load("""
- bucket
- queue
- table
- timer
""", Loader=yaml.FullLoader)

DefaultRoleIAM=yaml.load("""
- "logs:*"
""", Loader=yaml.FullLoader)

EventPollingRoleIAM=yaml.load("""
bucket: []
table:
  - "ddb:*"
queue:
  - "sqs:*"
timer: []
""", Loader=yaml.FullLoader)

def preprocess(config):
    def keyfn(component):
        return "%s/%s" % (component["type"],
                          component["name"])
    def is_non_functional(component, types=NonFunctionalTypes):
        return component["type"] in types
    def is_function(component):
        return component["type"]=="function"
    def filter_functions(components):
        return [component
                for component in components
                if is_function(component)]
    def is_api(component):
        return (is_function(component) and
                "api" in component)
    def is_event_handler(component):
        return (is_function(component) and
                "api" not in component)
    def filter_event_handlers(components):
        return [component
                for component in components
                if is_event_handler(component)]
    def validate_event_handler(func, nonfuncmap):
        nonfunckeys=nonfuncmap.keys()
        for attr in ["src", "dest"]:
            handlerkey=keyfn(func[attr])
            if handlerkey not in nonfunckeys:
                raise RuntimeError("%s not found" % handlerkey)
    def add_bucket_target(self, func, binding):
        self.setdefault("targets", [])
        targetnames=[target["name"]
                     for target in self["targets"]]
        if func["name"] in targetnames:
            raise RuntimeError("%s already mapped" % keyfn(self))
        target={"name": func["name"],
                "path": binding["path"]}
        self["targets"].append(target)
    def add_queue_target(self, func, binding):    
        if "target" in self:
            raise RuntimeError("%s already mapped" % keyfn(self))
        target={"name": func["name"]}
        if "batch" in binding:
            target["batch"]=binding["batch"]
        self["target"]=target
    def add_table_target(self, func, binding):    
        if "target" in self:
            raise RuntimeError("%s already mapped" % keyfn(self))
        target={"name": func["name"]}
        self["target"]=target
    def add_timer_target(self, func, binding):    
        if "target" in self:
            raise RuntimeError("%s already mapped" % keyfn(self))
        target={"name": func["name"]}
        self["target"]=target
    nonfuncmap={keyfn(component):component
                for component in config["components"]
                if is_non_functional(component)}    
    for func in filter_event_handlers(config["components"]):
        validate_event_handler(func, nonfuncmap)
        binding=func.pop("src")
        nonfunc=nonfuncmap[keyfn(binding)]
        targetfn=eval("add_%s_target" % nonfunc["type"])
        targetfn(self=nonfunc,
                 func=func,
                 binding=binding)
        # START TEMP CODE
        func.pop("dest")        
        # END TEMP CODE
        
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
