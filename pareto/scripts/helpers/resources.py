from botocore.exceptions import ValidationError

from pareto.helpers.text import text_left

import pandas as pd

import re

class Resource(dict):

    def __init__(self, resource):
        dict.__init__(self, resource)

    def lookup(self, attr, default=""):
        return self[attr] if attr in self else default
        
    def matches(self, term):
        for attr in self:
            if re.search(term, str(self[attr]), re.I):
                return True
        return False
        
class Resources(list):

    @classmethod
    def initialise(self, stackname, cf, filterfn=lambda x: True):
        def fetch_stack_resources(stackname, cf):
            try:
                return cf.describe_stack_resources(StackName=stackname)["StackResources"]
            except ValidationError:
                return []
        stacknames=[stack["StackName"]
                    for stack in cf.describe_stacks()["Stacks"]
                    if stack["StackName"].startswith(stackname)]
        resources=[]
        for stackname in stacknames:
            stackresources=fetch_stack_resources(stackname, cf)
            for _resource in stackresources:
                resource=Resource(_resource)
                if filterfn(resource):                    
                    resources.append(resource)
        return Resources(sorted(resources,
                             key=lambda x: x["Timestamp"]))

    def __init__(self, resources):
        list.__init__(self, resources)
    
    def table_repr(self, attrs):
        return pd.DataFrame([{attr: text_left(resource.lookup(attr))
                              for attr in attrs}
                             for resource in self])
    
if __name__=="__main__":
    pass
