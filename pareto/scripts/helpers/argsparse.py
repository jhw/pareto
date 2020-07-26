import os, re, yaml

def match_int(value):
    return re.search("^\\-?\\d+$", value)!=None
def match_float(value):
    return re.search("^\\-?\\d+\\.\\d+$", value)!=None
def match_bool(value):
    return re.search("^(true)|(false)$", value, re.I)!=None
def match_enum(value):
    return True
def match_str(value):
    return True
def match_file(value):
    return value.endswith(".yaml")
            
def parse_int(value):
    return int(value)
def parse_float(value):
    return float(value)
"""
>>> bool("false")
True
"""
def parse_bool(value):
    # return bool(value.lower().capitalize())
    return value.lower() not in ["0", "false"]
def parse_enum(value):
    return value
def parse_str(value):
    return value
def parse_file(value):
    if not os.path.exists(value):
        raise RuntimeError("file does not exist")
    return yaml.load(open(value, 'r'),
                     Loader=yaml.FullLoader)

def validate_int(value, item):
    pass
def validate_float(value, item):
    pass
def validate_bool(value, item):
    pass
def validate_enum(value, item):
    if value not in item["options"]:
        raise RuntimeError("Value is not a valid option")
def validate_str(value, item):
    pass
def validate_file(value, item):
    pass

def assert_length(fn):
    def wrapped(args, config):
        if len(args)!=len(config):
            raise RuntimeError("Please enter %s" % ", ".join((item["name"]
                                                              for item in config)))
        return fn(args, config)
    return wrapped
        
@assert_length
def argsparse(args, config):
    def match(fn):
        def wrapped(value, item):
            prefn=eval("match_%s" % item["type"])
            if not prefn(value):
                raise RuntimeError("%s type is invalid" % item["name"])
            return fn(value, item)
        return wrapped
    def validate(fn):
        def wrapped(value, item):
            resp=fn(value, item)
            postfn=eval("validate_%s" % item["type"])
            postfn(value, item)
            return resp
        return wrapped
    @match
    @validate
    def parse(value, item):
        fn=eval("parse_%s" % item["type"])
        return fn(value)
    return {item["name"]:parse(value, item)
            for value, item in zip(args, config)}

if __name__=="__main__":
    pass
