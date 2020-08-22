from pareto.components import *

ParamNames=yaml.safe_load("""
- app-name
- stage-name
- region
""")

def dash_resource(fn):
    def wrapped(**kwargs):
        component={k:v for k, v in zip(["Type", "Properties"],
                                       fn(**kwargs))}
        return (logical_id("%s-dash" % kwargs["name"]),
                component)
    return wrapped

@dash_resource
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
    name=resource_name({"name": kwargs["name"]})
    layout=grid_layout(kwargs["body"])    
    body=fn_sub(json.dumps(layout),
                {underscore(param): ref(param)
                 for param in ParamNames})
    props={"DashboardName": name,
           "DashboardBody": body}
    return "AWS::CloudWatch::Dashboard", props

if __name__=="__main__":
    pass
