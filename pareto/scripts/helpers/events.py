from botocore.exceptions import ValidationError

import pandas as pd

import re, yaml

DefaultAttrs=yaml.safe_load("""
- Timestamp
- StackName
- LogicalResourceId
- PhysicalResourceId
- ResourceType
- ResourceStatus
- ResourceStatusReason
""")

class Event(dict):

    def __init__(self, event):
        dict.__init__(self, event)

    def lookup(self, attr,
               default=""):
        return self[attr] if attr in self else default
        
    def matches(self, term,
                attrs=DefaultAttrs):
        for attr in attrs:
            if (attr in self and
                re.search(term, str(self[attr]), re.I)!=None):
                return True
        return False
        
class Events(list):

    @classmethod
    def initialise(self, stackname, cf, filterfn=lambda x: True):
        def fetch_stack_events(stackname, cf):
            try:
                return cf.describe_stack_events(StackName=stackname)["StackEvents"]
            except ValidationError:
                return []
        stacknames=[stack["StackName"]
                    for stack in cf.describe_stacks()["Stacks"]
                    if stack["StackName"].startswith(stackname)]
        events=[]
        for stackname in stacknames:
            stackevents=fetch_stack_events(stackname, cf)
            for _event in stackevents:
                event=Event(_event)
                if filterfn(event):                    
                    events.append(event)
        return Events(sorted(events,
                             key=lambda x: x["Timestamp"]))

    def __init__(self, events):
        list.__init__(self, events)
    
    @property
    def table_repr(self,
                   attrs=DefaultAttrs):
        return pd.DataFrame([{attr: event.lookup(attr)
                              for attr in attrs}
                             for event in self])
    
if __name__=="__main__":
    pass
