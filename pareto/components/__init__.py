import json, random, re, yaml

from pareto.template import *

def titleise(text):
    return " ".join([tok.capitalize()
                     for tok in re.split("\\-|\\_", text)])

def labelise(text):
    return "-".join([tok.lower()
                     for tok in re.split("\\s|\\_", text)])

def hungarorise(text):
    return "".join([tok.capitalize()
                    for tok in re.split("\\-|\\_", text)])    

def resource_name(kwargs):
    return "-".join([labelise(kwargs[attr])
                     for attr in ["app", "name", "stage"]])

def random_id(prefix, n=32):
    salt="".join([chr(65+int(26*random.random()))
                  for i in range(n)])
    return "%s-%s" % (prefix, salt)

def logical_id(name):
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
    def assert_values(fn):
        def wrapped(key, values, **kwargs):
            if (not isinstance(values, tuple) or
                len(values) < 2 or
                type(values[0])!=str or
                type(values[1])!=dict):
                raise RuntimeError("%s must return at least type, props" % key)
            return fn(key, values, **kwargs)
        return wrapped
    @assert_values
    def format_values(key, values, attrs=["Type", "Properties", "DependsOn"]):
        def format_value(k, v):
            return [logical_id(name) for name in v] if k=="DependsOn" else v
        return {k:format_value(k, v)
                for k, v in zip(attrs[:len(values)],
                                values)}
    def decorator(fn):
        def wrapped(*args, **kwargs):
            name="%s-%s" % (kwargs["name"],
                            suffix) if suffix else kwargs["name"]
            key=logical_id(name)
            values=fn(*args, **kwargs)
            return (key, format_values(key, values))
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

if __name__=="__main__":
    pass
