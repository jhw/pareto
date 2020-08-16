from botocore.exceptions import ValidationError

from pareto.helpers.text import text_left

import pandas as pd

import re

class Event(dict):

    def __init__(self, event):
        dict.__init__(self, event)

    def lookup(self, attr, default=""):
        return self[attr] if attr in self else default
        
    def matches(self, term):
        for attr in self:
            if re.search(term, str(self[attr]), re.I):
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
    
    def table_repr(self, attrs):
        return pd.DataFrame([{attr: text_left(str(event.lookup(attr)))
                              for attr in attrs}
                             for event in self])
    
if __name__=="__main__":
    pass
