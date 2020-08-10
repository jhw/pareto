import yaml

LookbackPermissions=yaml.safe_load("""
table:
- dynamodb:DescribeStream
- dynamodb:GetRecords
- dynamodb:GetShardIterator
- dynamodb:ListStreams
queue:
- sqs:DeleteMessage
- sqs:GetQueueAttributes
- sqs:ReceiveMessage
""")

def validate(config):
    def filter_names(config):
        names=[]
        for groupkey in config["components"]:
            for component in config["components"][groupkey]:
                names.append(component["name"])
        return names
    """
    - filter_action_refs should be genericised somehow
    """    
    def filter_action_refs(config):
        names=[]
        for groupkey in config["components"]:
            for component in config["components"][groupkey]:
                if "action" in component:
                    names.append(component["action"])
                elif "actions" in component:
                    names+=[action["name"]
                            for action in component["actions"]]
                elif "services" in component:
                    names+=component["services"]
        return names
    def validate_unique_names(config):
        names=filter_names(config)
        unames=list(set(names))
        if len(names)!=len(unames):
            raise RuntimeError("component names are not unique")
    def validate_action_refs(config):
        names=filter_names(config)
        for ref in filter_action_refs(config):
            if ref not in names:
                raise RuntimeError("ref %s not found in component names" % ref)
    validate_unique_names(config)
    validate_action_refs(config)

def assert_actions(fn):
    def wrapped(config):
        if "actions" in config["components"]:
            return fn(config)
    return wrapped
    
@assert_actions
def preprocessor(config):
    def filter_actions(config):
        return {action["name"]:action
                for action in config["components"]["actions"]}
    def filter_types(config):
        types={}
        for groupkey in config["components"]:
            for component in config["components"][groupkey]:
                if "action" in component:
                    types[component["action"]]=groupkey[:-1]
        return types
    actions, types = filter_actions(config), filter_types(config)
    for actionname, action in actions.items():
        if (actionname in types and
            types[actionname] in LookbackPermissions):
            action.setdefault("permissions", [])
            action["permissions"]+=LookbackPermissions[types[actionname]]

def preprocess(fn):
    def wrapped(config):
        validate(config)
        preprocessor(config)
        return fn(config)
    return wrapped
            
if __name__=="__main__":
    pass
