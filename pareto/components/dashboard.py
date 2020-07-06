from pareto.components import *

Root="pareto/charts"

"""
### Chart src

- navigate to main lambda dash for region
- select a lambda
- click Monitoring tab
- click on three vertical dots on top RHS side of a chart
- select View in Metrics
- click Source tab
"""

"""
### Dashboard src

- navigate to main cloudwatch dash for region
- click Dashboards
- select a dashboard
- Actions -> View/Edit Source
"""

def titleise(text):
    return " ".join([tok.capitalize()
                     for tok in re.split("\\-|\\_", text)])

def synth_dashboard(**kwargs):
    def init_chart(kwargs, src):
        def init_metrics(chart):
            metrics=chart["metrics"]
            name=resource_id(kwargs)
            for key in ["FunctionName",
                        "Resource"]:
                i=metrics[0].index(key)
                metrics[0][i+1]=name
        def init_title(chart):
            suffix=src.split("/")[-1].split(".")[0].split("_")[-1]
            chart["title"]="%s %s" % (titleise(kwargs["name"]),
                                      suffix.capitalize())
        def init_region(chart):
            chart["region"]=kwargs["region"]
        chart=yaml.load(open(src).read(),
                        Loader=yaml.FullLoader)
        for fn in [init_metrics,
                   init_title,
                   init_region]:
            fn(chart)
        return chart
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
    @resource()
    def Dashboard(root=Root, **kwargs):
        charts=[[init_chart(component, "%s/%s" % (root, src))
                 for src in ["function/invocations.yaml",
                             "function/duration.yaml",
                             "function/errors.yaml"]]
                for component in kwargs["components"]
                if component["type"]=="function"]
        layout=grid_layout(charts)
        props={"DashboardName": resource_id(kwargs),
               "DashboardBody": json.dumps(layout)}
        return "AWS::CloudWatch::Dashboard", props
    return Template(resources=[Dashboard(**kwargs)])

if __name__=="__main__":
    pass
