import json

class Element(list):

    def __init__(self, items):
        list.__init__(self, items)

    def update(self, items):
        self+=items

    def render(self):
        return dict(self) # because component returns tuples

class Dashboard(list):

    def __init__(self, items):
        list.__init__(self, items)

    def update(self, items):
        self+=items

    def grid_layout(self):
        return self

    def render(self):
        layout=self.grid_layout()
        props={"DashboardBody": json.dumps(layout)}
        attrs={"Type": "AWS::CloudWatch::Dashboard",
               "Properties": props}
        return {"Dashboard": attrs} # to match Element.render output
            
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
            struct["resources"].update(self.dashboard.render())
        return {k.capitalize():v
                for k, v in struct.items()}
            
if __name__=="__main__":
    pass
