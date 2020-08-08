"""
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cloudformation-limits.html
"""

import json, re, yaml

Metrics={"resources": (lambda t: len(t["Resources"])/200),
         "outputs": (lambda t: len(t["Outputs"])/60),
         "template_size": (lambda t: len(json.dumps(t))/51200)}

class Template(dict):

    def __init__(self, items={}):
        dict.__init__(self)
        for attr in ["Parameters",
                     "Resources",
                     "Outputs"]:
            items.setdefault(attr, {})
        self.update(items)
        
    def update(self, items):
        for k, v in items.items():
            self.setdefault(k, {})
            self[k].update(dict(v))
        
    @property
    def metrics(self, metrics=Metrics):
        return {metrickey: metricfn(self)
                for metrickey, metricfn in metrics.items()}

    @property
    def resource_ids(self):
        ids=[]
        for attr in ["Resources", "Parameters"]:
            if attr in self:
                ids+=self[attr].keys()
        return ids
    
    @property
    def resource_refs(self):
        def is_new_ref(key, element, refs):
            return (key=="Ref" and
                    type(element)==str and
                    element not in refs)
        def is_new_getatt(key, element, refs):
            return (key=="Fn::GetAtt" and
                    type(element)==list and
                    type(element[0])==str and
                    element[0] not in refs)
        def filter_refs(element, refs):
            if isinstance(element, list):
                for subelement in element:
                    filter_refs(subelement, refs)
            elif isinstance(element, dict):
                for key, subelement in element.items():
                    if is_new_ref(key, subelement, refs):
                        # print ("ref: %s" % subelement)
                        refs.append(subelement)
                    elif is_new_getatt(key, subelement, refs):
                        # print ("getatt: %s" % subelement[0])
                        refs.append(subelement[0])
                    else:
                        filter_refs(subelement, refs)
                else:
                    pass
        refs=[]
        filter_refs(self, refs)
        return refs

    """
    - some CF fields, notably ApiGateway HTTP header related ones, explicity require single quoted string values
    - and if you encode (backquote) those values they will be rejected :-/    
    """
    
    @property
    def json_repr(self):
        class SingleQuoteEncoder(json.JSONEncoder):
            def default(self, obj):
                if (isinstance(obj, str) and
                    "'" in obj):
                    return obj
                return json.JSONEncoder.default(self, obj)
        return json.dumps(self,
                          cls=SingleQuoteEncoder).encode("utf-8")

    """
    - pyyaml will encode `"'` as `'''` :-/
    - not strictly required that this needs to be fixed (as only JSON templates are pushed to S3), but just for consistency with JSON when debugging via YAML templates
    """
    
    @property
    def yaml_repr(self):
        class Counter:
            def __init__(self):
                self.value=0
            def increment(self):
                self.value+=1
        def count(fn):
            counter=Counter()
            def wrapped(match):
                resp=fn(match, counter)
                counter.increment()
                return resp
            return wrapped
        @count
        def matcher(match, counter):
            return "\"'" if 0==counter.value % 2 else "'\""
        def unescape_single_quotes(text):
            return re.sub("'''", matcher, text)
        yaml.SafeDumper.ignore_aliases=lambda *args : True
        return unescape_single_quotes(yaml.safe_dump(dict(self), # remove Template class
                                                     default_flow_style=False))
    
if __name__=="__main__":
    pass
