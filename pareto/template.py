class Element(list):

    def __init__(self, items):
        list.__init__(self, items)

    def update(self, items):
        self+=items

    def render(self):
        return dict(self) # because component returns tuples

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

    def render(self):
        return self
        
class Template:

    def __init__(self,
                 parameters=[],
                 resources=[],
                 outputs=[],
                 dashboard=[],
                 **kwargs):
        self.parameters=Element(parameters)
        self.resources=Element(resources)
        self.outputs=Element(outputs)
        self.dashboard=Dashboard(dashboard)

    def update(self, template):
        for attr in ["parameters",
                     "resources",
                     "outputs",
                     "dashboard"]:
            parent=getattr(self, attr)
            parent.update(getattr(template, attr))

    def render(self):
        struct={attr:getattr(self, attr).render()
                for attr in ["parameters",
                             "resources",
                             "outputs"]
                if getattr(self, attr)!=[]}
        if self.dashboard!=[]:
            print (self.dashboard.render())
        return {k.capitalize():v
                for k, v in struct.items()}
            
if __name__=="__main__":
    pass
