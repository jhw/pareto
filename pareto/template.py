"""
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cloudformation-limits.html
"""

import json

Metrics={"resources": (lambda t: len(t["Resources"])/200),
         "outputs": (lambda t: len(t["Outputs"])/60),
         "template_size": (lambda t: len(json.dumps(t))/51200)}

class Template(dict):

    def __init__(self, items={}):
        dict.__init__(self, items)

    @property
    def metrics(self, metrics=Metrics):
        return {metrickey: metricfn(self)
                for metrickey, metricfn in metrics.items()}
            
if __name__=="__main__":
    pass
