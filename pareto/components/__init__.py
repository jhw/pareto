from pareto.helpers.cloudformation.utils import *

import json, yaml

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
    def validate_type(fn):
        def wrapped(k, v):
            if (k=="Type" and
                not re.search("^AWS\\:\\:\\w+\\:\\:\\w+$", v)):
                raise RuntimeError("%s is invalid type" % v)
            return fn(k, v)
        return wrapped
    @assert_values
    def format_values(key, values, attrs=["Type", "Properties", "DependsOn"]):
        @validate_type
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
