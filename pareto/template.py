class Element(list):

    def __init__(self, items):
        list.__init__(self, items)

    def update(self, items):
        self+=items

    """
    - dict() because components return tuples
    """
        
    def render(self):
        return dict(self)

class Parameters(Element):

    def __init__(self, items):
        Element.__init__(self, items)

class Resources(Element):

    def __init__(self, items):
        Element.__init__(self, items)

class Outputs(Element):

    def __init__(self, items):
        Element.__init__(self, items)

"""
- dashboard does not extend Element as has to be rendered to a resource
"""

"""
@resource()
def Dashboard(root=Root, **kwargs):
    charts=[[init_chart(component, "%s/%s" % (root, src))
             for src in ["function/invocations.yaml",
                         "function/duration.yaml",
                         "function/errors.yaml"]]
            for component in kwargs["components"]
            if "action" in component]
    layout=grid_layout(charts)
    props={"DashboardName": resource_name(kwargs),
           "DashboardBody": json.dumps(layout)}
    return "AWS::CloudWatch::Dashboard", props
"""

class Dashboard(list):

    def __init__(self, items):
        list.__init__(self, items)

    def update(self, items):
        self+=items

    """
    - render() needs to return something that looks like the old dash class
    """
        
    def render(self):
        return dict(self)
        
class Template:

    def __init__(self,
                 parameters=[],
                 resources=[],
                 outputs=[],
                 dashboard=[],
                 **kwargs):
        self.parameters=Parameters(parameters)
        self.resources=Resources(resources)
        self.outputs=Outputs(outputs)
        self.dashboard=Dashboard(dashboard)

    def update(self, template):
        for attr in ["parameters",
                     "resources",
                     "outputs",
                     "dashboard"]:
            parent=getattr(self, attr)
            parent.update(getattr(template, attr))

    """
    - dash needs to be appended as to resource rather than rendered as element
    """
            
    def render(self):
        return {attr.capitalize():getattr(self, attr).render()
                for attr in ["parameters",
                             "resources",
                             "outputs",
                             "dashboard"]
                if len(getattr(self, attr)) > 0}
            
if __name__=="__main__":
    pass
