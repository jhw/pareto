import json, re, yaml

def resource_id(**kwargs):
    def labelise(text):
        return "-".join([tok.lower()
                         for tok in re.split("\\s|\\_", text)])    
    return "-".join([labelise(kwargs[attr])
                     for attr in ["app", "name", "stage"]])

def logical_id(name):
    def hungarorise(text):
        return "".join([tok.capitalize()
                        for tok in re.split("\\-|\\_", text)])    
    return hungarorise(name)

def ref(name):
    return {"Ref": logical_id(name)}

def fn_getatt(name, attr):
    return {"Fn::GetAtt": [logical_id(name), attr]}

def fn_join(args, delimiter=""):    
    return {"Fn::Join": [delimiter, args]}

def fn_sub(expr, kwargs={}):    
    return {"Fn::Sub": [expr, kwargs]}

def parameter(name, type_="String"):
    return (logical_id(name), {"Type": type_})

def resource(suffix=None):
    def format_depends(v):
        return [logical_id(name)
                for name in v]
    def format_value(k, v):
        return format_depends(v) if k=="DependsOn" else v
    def decorator(fn):
        def wrapped(attrs=["Type", "Properties", "DependsOn"],
                    *args, **kwargs):
            name="%s-%s" % (kwargs["name"],
                            suffix) if suffix else kwargs["name"]
            key=logical_id(name)
            values=fn(*args, **kwargs)
            return (key, {k:format_value(k, v)
                          for k, v in zip(attrs[:len(values)],
                                          values)})
        return wrapped
    return decorator

def output(suffix=None):
    def decorator(fn):
        def wrapped(*args, **kwargs):
            name="%s-%s" % (kwargs["name"],
                            suffix) if suffix else kwargs["name"]
            return (logical_id(name),
                    {"Value": fn(*args, **kwargs)})
        return wrapped
    return decorator

class Template(dict):

    def __init__(self, **kwargs):
        dict.__init__(self, kwargs)
        for attr in ["parameters",
                     "resources",
                     "outputs"]:
            self.setdefault(attr, [])

    def update(self, template):
        for attr in self.keys():
            if attr in template:
                self[attr]+=template[attr]

    def render(self):
        """
        - dict() required because values are lists of tuples
        """
        return {k.capitalize():dict(v)
                for k, v in self.items()
                if len(v) > 0}
                
if __name__=="__main__":
    pass
