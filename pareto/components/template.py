from pareto.components import *

from pareto.components.dashboard import Dashboard

from collections import OrderedDict

import io, ruamel.yaml

TemplateVersion="2010-09-09"

Parameters, Outputs, Resources, Charts = "Parameters", "Outputs", "Resources", "Charts"

AppName, StageName = "AppName", "StageName"

"""
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cloudformation-limits.html
"""

Metrics={"parameters": (lambda t: len(t.Parameters)/200),
         "resources": (lambda t: len(t.Resources)/500),
         "outputs": (lambda t: len(t.Outputs)/200),
         "template_size": (lambda t: len(json.dumps(t.render()))/1000000)}

def clone_attr(v):
    return list(v) if isinstance(v, list) else dict(v)

class Template:
    
    Attrs=[Parameters, Outputs, Resources, Charts]
    
    def __init__(self, name):
        self.name=name
        def default_value(k):
            return [] if k=="Charts" else {}
        for attr in self.Attrs:
            setattr(self, attr, default_value(attr))

    def clone(self, name):
        template=Template(name)
        for attr in self.Attrs:
            setattr(template, attr, clone_attr(getattr(self, attr)))
        return template

    def fragment(self):
        def charts_name(name):
            tokens=name.split("-")
            return "-".join(tokens[:-1]+["charts"]+[tokens[-1]])
        charts=Template(charts_name(self.name))
        noncharts=Template(self.name)
        for attr in self.Attrs:
            if attr==Parameters:
                setattr(noncharts, attr, clone_attr(getattr(self, attr)))
                setattr(charts, attr, {k: v for k, v in clone_attr(getattr(self, attr)).items() if k in [AppName, StageName]})
            elif attr==Charts:
                setattr(charts, attr, clone_attr(getattr(self, attr)))
            else: # Resources, Outputs
                setattr(noncharts, attr, clone_attr(getattr(self, attr)))
        templates=[noncharts]
        if len(charts.Charts) > 0:
            templates.append(charts)
        return templates

    def assert_keywords(fn):
        def wrapped(self, **kwargs):
            for k in kwargs:
                if k not in self.Attrs:
                    raise RuntimeError("Unknown template keyword %s (template takes capitalized keywords only)" % k)
            return fn(self, **kwargs)
        return wrapped
                
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
        struct=OrderedDict()
        struct["AWSTemplateFormatVersion"]=TemplateVersion
        if self.name:
            struct["Description"]=self.name
        for attr in self.Attrs:
            if attr=="Charts":
                continue
            struct[attr]=getattr(self, attr)
        if self.Charts!=[]:
            dash=Dashboard(**{"name": self.name,
                              "body": self.Charts})
            struct["Resources"].update(dict([dash]))
        return struct

    def filter_logical_ids(self, struct, attrs):
        ids=[]
        for attr in attrs:
            ids+=struct[attr].keys()
        return ids
    
    def filter_logical_id_refs(self, struct):
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
        filter_refs(struct, refs)
        return list(refs)

    def validate_params(self, struct):
        ids=self.filter_logical_ids(struct,
                                    ["Parameters"])
        refs=self.filter_logical_id_refs(struct)
        for id in ids:
            if id not in refs:
                raise RuntimeError("%s template has unused parameter" % (self.name, id))
    
    def validate_logical_ids(self, struct):
        ids=self.filter_logical_ids(struct,
                                    ["Parameters",
                                     "Resources"])
        refs=self.filter_logical_id_refs(struct)
        for ref in refs:
            if ref not in ids:
                raise RuntimeError("bad reference to %s in %s template" % (ref, self.name))

    """
    - \\w+ will match `foo_bar` but not `Foo::Bar`
    """
            
    def validate_string_refs(self, struct):
        def filter_refs(element):
            return list(set([ref[2:-1]
                             for ref in re.findall("\\$\\{\\w+\\}", element[0])]))
        def filter_keys(element):
            return list(element[1].keys())
        def to_string(values):
            return "/".join(sorted(values))
        def iterparse(element):
            if isinstance(element, list):
                for subelement in element:
                    iterparse(subelement)
            elif isinstance(element, dict):
                for key, subelement in element.items():
                    if key=="Fn::Sub":
                        refs=to_string(filter_refs(subelement))
                        keys=to_string(filter_keys(subelement))
                        # print ("%s :: %s" % (refs, keys))
                        if refs!=keys:
                            raise RuntimeError("fn::sub ref mismatch in template %s - %s vs %s" % (self.name, refs, keys))
                    else:
                        iterparse(subelement)
        iterparse(struct)
        
    def validate(self):
        struct=self.render()
        self.validate_logical_ids(struct)
        self.validate_string_refs(struct)
    
    @property
    def metrics(self, metrics=Metrics):
        return {metrickey: metricfn(self)
                for metrickey, metricfn in metrics.items()}
      
    @property
    def json_repr(self):
        return json.dumps(self.render())

    """
    - https://stackoverflow.com/questions/53874345/how-do-i-dump-an-ordereddict-out-as-a-yaml-file
    """
    
    @property
    def yaml_repr(self):
        from ruamel.yaml.representer import RoundTripRepresenter
        class MyRepresenter(RoundTripRepresenter):
            pass
        ruamel.yaml.add_representer(OrderedDict,
                                    MyRepresenter.represent_dict, 
                                    representer=MyRepresenter)
        yaml=ruamel.yaml.YAML()
        yaml.Representer=MyRepresenter
        yaml.representer.ignore_aliases=lambda *data: True
        yaml.preserve_quotes=True
        buf=io.StringIO()
        yaml.dump(self.render(), buf)
        return buf.getvalue()
    
if __name__=="__main__":
    pass
