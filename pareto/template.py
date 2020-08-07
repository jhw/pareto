"""
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cloudformation-limits.html
"""

import json

Metrics={"resources": (lambda t: len(t.resources)/200),
         "outputs": (lambda t: len(t.outputs)/60),
         "template_size": (lambda t: len(json.dumps(t.render()))/51200)}

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

    @property
    def metrics(self, metrics=Metrics):
        return {metrickey: metricfn(self)
                for metrickey, metricfn in metrics.items()}

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
