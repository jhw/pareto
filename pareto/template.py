"""
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cloudformation-limits.html
"""

import json, re, yaml

Metrics={"resources": (lambda t: len(t.Resources)/200),
         "outputs": (lambda t: len(t.Outputs)/60),
         "template_size": (lambda t: len(json.dumps(t.render()))/51200)}

"""
- a simplified version of @resource from components/__init__.py as dash is a special case and you can't seem to importr from nested package without circularity
- to maintain consistency with how non- dash components are treated
"""

def resource(fn):
    def wrapped(**kwargs):
        component={k:v for k, v in zip(["Type", "Properties"],
                                       fn(**kwargs))}
        return ("MyDash", component) # TEMP
    return wrapped

@resource
def Dashboard(**kwargs):
    def grid_layout(charts,
                    pagewidth=24,
                    heightratio=0.75):
        x, y, widgets = 0, 0, []
        for row in charts:
            width=int(pagewidth/len(row))
            height=int(heightratio*width)
            for chart in row:
                widget={"type": "metric",
                        "x": x,
                        "y": y,
                        "width": width,
                        "height": height,
                        "properties": chart}
                widgets.append(widget)
                x+=width
            y+=height
            x=0 # NB reset
        return {"widgets": widgets}
    layout=grid_layout(kwargs["body"])
    props={"DashboardName": kwargs["name"],
           "DashboardBody": json.dumps(layout)}
    return "AWS::CloudWatch::Dashboard", props

class Template:
    
    Attrs=["Parameters", "Resources", "Outputs", "Charts"]
    
    def assert_keywords(fn):
        def wrapped(self, **kwargs):
            for k in kwargs:
                if k not in self.Attrs:
                    raise RuntimeError("Unknown template keyword %s (template takes capitalized keywords only" % k)
            return fn(self, **kwargs)
        return wrapped
    
    @assert_keywords
    def __init__(self, **kwargs):
        def default_value(k):
            return [] if k=="Charts" else {}
        for attr in self.Attrs:
            setattr(self, attr, default_value(attr))
        self.update(**kwargs)

    @assert_keywords
    def update(self, **kwargs):
        def listify(fn):
            def wrapped(v):
                return [v] if isinstance(v, tuple) else v
            return wrapped
        @listify
        def format_value(v):
            return dict(v)
        for k, v in kwargs.items():
            if k!="Charts":
                getattr(self, k).update(format_value(v))
            else:
                getattr(self, k).append(v)                

    def render(self):
        struct={attr: getattr(self, attr)
                for attr in self.Attrs
                if attr!="Charts"}
        if self.Charts!=[]:
            dash=Dashboard(**{"name": "foobar", # TEMP
                              "body": self.Charts})
            struct["Resources"].update(dict([dash]))
        return struct
            
    @property
    def resource_ids(self):
        ids=[]
        for attr in ["Resources", "Parameters"]:
            ids+=getattr(self, attr).keys()
        return ids
    
    @property
    def resource_refs(self):
        def is_ref(key, element):
            return (key=="Ref" and
                    type(element)==str)
        def is_getatt(key, element):
            return (key=="Fn::GetAtt" and
                    type(element)==list and
                    type(element[0])==str)
        def filter_refs(element, refs):
            if isinstance(element, list):
                for subelement in element:
                    filter_refs(subelement, refs)
            elif isinstance(element, dict):
                for key, subelement in element.items():
                    if is_ref(key, subelement):
                        refs.add(subelement)
                    elif is_getatt(key, subelement):
                        refs.add(subelement[0])
                    else:
                        filter_refs(subelement, refs)
        refs=set()
        filter_refs(self.render(), refs)
        return list(refs)

    @property
    def metrics(self, metrics=Metrics):
        return {metrickey: metricfn(self)
                for metrickey, metricfn in metrics.items()}
      
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
        return json.dumps(self.render(),
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
        return unescape_single_quotes(yaml.safe_dump(self.render(),
                                                     default_flow_style=False))
    
if __name__=="__main__":
    pass
