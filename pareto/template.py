import json

class Element(list):

    def __init__(self, items):
        list.__init__(self, items)

    def update(self, items):
        self+=items

    def render(self):
        return dict(self) # because component returns tuples

class Template:

    def __init__(self,
                 parameters=[],
                 resources=[],
                 outputs=[],
                 charts=[],
                 **kwargs):
        self.parameters=Element(parameters)
        self.resources=Element(resources)
        self.outputs=Element(outputs)
        self.charts=Element(charts)

    def update(self, template):
        for attr in ["parameters",
                     "resources",
                     "outputs",
                     "charts"]:
            parent=getattr(self, attr)
            parent.update(getattr(template, attr))

    def render(self):
        struct={attr:getattr(self, attr).render()
                for attr in ["parameters",
                             "resources",
                             "outputs"]
                if getattr(self, attr)!=[]}
        return {k.capitalize():v
                for k, v in struct.items()}
            
if __name__=="__main__":
    pass
