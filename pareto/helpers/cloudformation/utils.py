from pareto.helpers.text import *

import random

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

def resource_name(kwargs):
    expr="-".join(["${app_name}",
                   labelise(kwargs["name"]),
                   "${stage_name}"])    
    return fn_sub(expr,
                  {"app_name": ref("app-name"),
                   "stage_name": ref("stage-name")})

def random_id(prefix, n=32):
    salt="".join([chr(65+int(26*random.random()))
                  for i in range(n)])
    return "%s-%s" % (prefix, salt)
