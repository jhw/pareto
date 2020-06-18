import os, sys, yaml

def preprocess(config):
    def keyfn(component):
        return "%s/%s" % (component["type"],
                          component["name"])
    def is_function(component):
        return component["type"]=="function"
    def is_handler(component):
        return (is_function(component) and
                "api" not in component)
    def is_target(component):
        return component["type"] in ["bucket",
                                     "table",
                                     "queue"]
    def init_permissions(handler, required=["logs:*"]):
        permissions=handler.pop("permissions") if "permissions" in handler else []
        for permission in required:
            if permission not in permissions:
                permissions.append(permission)
        handler.setdefault("iam", {})
        handler["iam"].setdefault("permissions", permissions)
    def validate_handler(component, handlerkeys):
        for attr in ["src", "dest"]:
            handlerkey=keyfn(component[attr])
            if handlerkey not in handlerkeys:
                raise RuntimeError("%s not found" % handlerkey)
    def map_bucket(handler, bucket, target):
        bucket.setdefault("targets", [])
        bucket["targets"].append({"name": handler["name"],
                                    "path": target["path"]})
    def map_table(handler, table, target):
        if "target" in table:
            raise RuntimeError("%s already mapped" % keyfn(table))
        table["target"]={"name": handler["name"]}
    def map_queue(handler, queue, target):
        if "target" in queue:
            raise RuntimeError("%s already mapped" % keyfn(queue))
        queue["target"]={"name": handler["name"]}
    def add_permissions(handler, target,
                        permissions={"bucket": [],
                                     "table": ["ddb:*"],
                                     "queue": ["sqs:*"]}):
        for permission in permissions[target["type"]]:
            if permission not in handler["iam"]["permissions"]:
                handler["iam"]["permissions"].append(permission)
    targetmap={keyfn(component):component
               for component in config["components"]
               if is_target(component)}
    for component in config["components"]:
        if not is_function(component):
            continue
        init_permissions(component)
        if not is_handler(component):
            continue
        validate_handler(component, targetmap.keys())
        for attr in ["src", "dest"]:
            target=component.pop(attr)
            key=keyfn(target)
            add_permissions(component, target)
            if attr=="src":
                mapfn=eval("map_%s" % target["type"])
                mapfn(component, targetmap[key], target)
        
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
