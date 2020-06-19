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
    def is_function(component):
        return component["type"]=="function"
    def is_api(component):
        return (is_function(component) and
                "api" in component)
    def is_event_handler(component):
        return (is_function(component) and
                "api" not in component)
    def validate_event_handler(component, nonfunckeys):
        for attr in ["src", "dest"]:
            handlerkey=keyfn(component[attr])
            if handlerkey not in nonfunckeys:
                raise RuntimeError("%s not found" % handlerkey)
    def is_non_functional(component, types=NonFunctionalTypes):
        return component["type"] in types
    def init_role_iam(component, required=DefaultRoleIAM):
        permissions=component.pop("permissions") if "permissions" in component else []
        for permission in required:
            if permission not in permissions:
                permissions.append(permission)
        component.setdefault("iam", {})
        component["iam"].setdefault("permissions", permissions)
    def update_role_iam(component, target,
                        permissions=EventPollingRoleIAM):
        for permission in permissions[target["type"]]:
            if permission not in component["iam"]["permissions"]:
                component["iam"]["permissions"].append(permission)
    def set_target(self, component, target):    
        if "target" in self:
            raise RuntimeError("%s already mapped" % keyfn(self))
        self["target"]={"name": component["name"]}
    def add_target(self, component, target):
        self.setdefault("targets", [])
        targetnames=[target["name"]
                     for target in self["targets"]]
        if component["name"] in targetnames:
            raise RuntimeError("%s already mapped" % keyfn(self))
        self["targets"].append({"name": component["name"],
                                "path": target["path"]})
    def add_bucket_target(self, component, target):
        add_target(self, component, target)
    def add_table_target(self, component, target):
        set_target(self, component, target)
    def add_queue_target(self, component, target):
        set_target(self, component, target)
    def add_timer_target(self, component, target):
        set_target(self, component, target)        
    nonfuncmap={keyfn(component):component
               for component in config["components"]
               if is_non_functional(component)}
    for component in config["components"]:
        if not is_function(component):
            continue
        init_role_iam(component)
        if not is_event_handler(component):
            continue
        validate_event_handler(component, nonfuncmap.keys())
        for attr in ["src", "dest"]:
            target=component.pop(attr)
            key=keyfn(target)
            update_role_iam(component, target)
            if attr=="src":
                targetfn=eval("add_%s_target" % target["type"])
                targetfn(nonfuncmap[key], component, target)
        
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
