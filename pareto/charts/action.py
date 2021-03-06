from pareto.charts import *

from pareto.components import titleise

import re, yaml

"""
- to get function chart source
- navigate to main lambda dash for region
- select a lambda
- click Monitoring tab
- click on three vertical dots on top RHS side of a chart
- select View in Metrics
- click Source tab
"""

InvocationsChart="""
metrics:
- - AWS/Lambda
  - Invocations
  - FunctionName
  - {name}
  - Resource
  - {name}
  - stat: Sum
region: "${{AWS::Region}}"
stacked: false
title: {title}
view: timeSeries
"""

DurationChart="""
metrics:
- - AWS/Lambda
  - Duration
  - FunctionName
  - {name}
  - Resource
  - {name}
  - stat: Minimum
- - '...'
  - stat: Average
- - '...'
  - stat: Maximum
region: ${{AWS::Region}}
stacked: false
title: {title}
view: timeSeries
"""

ErrorsChart="""
metrics:
- - AWS/Lambda
  - Errors
  - FunctionName
  - {name}
  - Resource
  - {name}
  - color: '#d13212'
    id: errors
    stat: Sum
- - .
  - Invocations
  - .
  - .
  - .
  - .
  - id: invocations
    stat: Sum
    visible: false
- - expression: 100 - 100 * errors / MAX([errors, invocations])
    id: availability
    label: Success rate (%)
    region: ${{AWS::Region}}
    yAxis: right
region: ${{AWS::Region}}
stacked: false
title: {title}
view: timeSeries
yAxis:
  right:
    max: 100
"""

Charts={"invocations": InvocationsChart,
        "duration": DurationChart,
        "errors": ErrorsChart}

def ActionCharts(charts=Charts, **kwargs):
    def init_chart(key, chart, kwargs):
        chartkwargs={"name": resource_name(kwargs),
                     "title": titleise("%s-%s" % (kwargs["name"], key))}
        return yaml.safe_load(chart.format(**chartkwargs))
    return [init_chart(key, chart, kwargs)
            for key, chart in charts.items()]
    
if __name__=="__main__":
    kwargs={"app": "hello",
            "name": "foobar",
            "stage": "dev"}
    print (ActionCharts(**kwargs))
