from pareto.helpers.text import singularise

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
        return {singularise(key): [component["name"]
                                   for component in config["components"][key]]
                for key in config["components"]}
    def filter_refs(config, types):
        def listify(fn):
            def wrapped(v, attr, refs):
                if not isinstance(v, list):
                    v=[v]
                return fn(v, attr, refs)
            return wrapped
        def item_name(item):  
            return item["name"] if isinstance(item, dict) else item
        @listify        
        def add_refs(v, attr, refs):
            refs.setdefault(attr, [])
            refs[attr]+=[item_name(item)
                         for item in v]
        def filter_attrs(fn, reject=["staging"]):
            def wrapped(k, v, types, refs):
                if k not in reject:
                    return fn(k, v, types, refs)
            return wrapped
        @filter_attrs
        def handle_dict(k, v, types, refs):
            attr=singularise(k)
            if attr in types:
                add_refs(v, attr, refs)
            else:
                filter_refs(v, types, refs)
        def filter_refs(struct, types, refs):
            if isinstance(struct, dict):
                for k, v in struct.items():
                    handle_dict(k, v, types, refs)
            elif isinstance(struct, list):
                for v in struct:
                    filter_refs(v, types, refs)                    
            else:
                pass
        refs={}
        for key in config["components"]:
            for component in config["components"][key]:
                filter_refs(component, names, refs)
        return refs
    names=filter_names(config)
    print (names)
    refs=filter_refs(config, list(names.keys()))
    print (refs)
    
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
