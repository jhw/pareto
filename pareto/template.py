import json

class Template:

    def __init__(self,
                 parameters=[],
                 resources=[],
                 outputs=[],
                 charts=[]):
        self.parameters=list(parameters)
        self.resources=list(resources)
        self.outputs=list(outputs)
        self.charts=list(charts)

    def update(self, template):
        for attr in ["parameters",
                     "resources",
                     "outputs",
                     "charts"]:
            parent=getattr(self, attr)
            parent+=getattr(template, attr)

    def render(self):
        struct={attr:dict(getattr(self, attr))
                for attr in ["parameters",
                             "resources",
                             "outputs"]
                if getattr(self, attr)!=[]}
        return {k.capitalize():v
                for k, v in struct.items()}
            
if __name__=="__main__":
    pass
