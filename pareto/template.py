import json

class Element(list):

    def __init__(self, items):
        list.__init__(self, items)

    def update(self, items):
        self+=items

    def render(self):
        return dict(self) # because component returns tuples

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
    
class Template:

    def __init__(self,
                 name=None,
                 parameters=[],
                 resources=[],
                 outputs=[],
                 **kwargs):
        self.name=name
        self.parameters=Element(parameters)
        self.resources=Element(resources)
        self.outputs=Element(outputs)

    def update(self, template):
        for attr in ["parameters",
                     "resources",
                     "outputs"]:
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
