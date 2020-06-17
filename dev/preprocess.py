import os, sys, yaml

def preprocess(config):
    def keyfn(component):
        return "%s/%s" % (component["type"],
                          component["name"])
    def is_handler(component):
        return (component["type"]=="function" and
                "api" not in component)
    def is_source(component):
        return component["type"] in ["bucket",
                                     "table",
                                     "queue"]
    def validate_handler(component, handlerkeys):
        for attr in ["src", "dest"]:
            handlerkey=keyfn(component[attr])
            if handlerkey not in handlerkeys:
                raise RuntimeError("%s not found" % handlerkey)
    def map_bucket(handler, bucket, src):
        bucket.setdefault("functions", [])
        bucket["functions"].append({"name": handler["name"],
                                    "path": src["path"]})
    def map_table(handler, table, src):
        if "function" in table:
            raise RuntimeError("%s already mapped" % keyfn(table))
        table["function"]=handler["name"]
    def map_queue(handler, queue, src):
        if "function" in queue:
            raise RuntimeError("%s already mapped" % keyfn(queue))
        queue["function"]=handler["name"]
    def add_map_permissions(handler, src,
                        permissions={"bucket": [],
                                     "table": ["ddb:*"],
                                     "queue": ["sqs:*"]}):
        handler.setdefault("iam", {})
        handler["iam"].setdefault("permissions", [])
        handler["iam"]["permissions"]+=permissions[src["type"]]
    srcmap={keyfn(component):component
            for component in config["components"]
            if is_source(component)}
    for component in config["components"]:
        if not is_handler(component):
            continue
        validate_handler(component, srcmap.keys())
        src=component.pop("src")
        mapfn=eval("map_%s" % src["type"])
        srckey=keyfn(src)
        mapfn(component, srcmap[srckey], src)
        add_map_permissions(component, src)
        component.pop("dest")
        
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
        print (yaml.safe_dump(config,
                              default_flow_style=False))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
