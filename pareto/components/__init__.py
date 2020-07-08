import json, random, re, yaml

def resource_name(kwargs):
    def labelise(text):
        return "-".join([tok.lower()
                         for tok in re.split("\\s|\\_", text)])
    return "-".join([labelise(kwargs[attr])
                     for attr in ["app", "name", "stage"]])

def random_name(prefix, n=32):
    salt="".join([chr(65+int(26*random.random()))
                  for i in range(n)])
    return "%s-%s" % (prefix, salt)

def logical_id(name):
    def hungarorise(text):
        return "".join([tok.capitalize()
                        for tok in re.split("\\-|\\_", text)])    
    return hungarorise(name)

def ref(name):
    return {"Ref": logical_id(name)}

def fn_getatt(name, attr):
    return {"Fn::GetAtt": [logical_id(name), attr]}

def fn_sub(expr, kwargs={}):    
    return {"Fn::Sub": [expr, kwargs]}

def parameter(name, type_="String"):
    return (logical_id(name), {"Type": type_})

def resource(suffix=None):
    def fill_in_props(fn):
        def wrapped(values, **kwargs):
            if not isinstance(values, tuple):
                values=(values, {})
            return fn(values, **kwargs)
        return wrapped
    def format_value(k, v):
        def format_depends(v):
            return [logical_id(name)
                    for name in v]
        return format_depends(v) if k=="DependsOn" else v
    @fill_in_props
    def format_values(values,
                      attrs=["Type", "Properties", "DependsOn"]):
        return {k:format_value(k, v)
                for k, v in zip(attrs[:len(values)],
                                values)}
    def decorator(fn):
        def wrapped(*args, **kwargs):
            name="%s-%s" % (kwargs["name"],
                            suffix) if suffix else kwargs["name"]
            key=logical_id(name)
            values=fn(*args, **kwargs)
            return (key, format_values(values))
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
