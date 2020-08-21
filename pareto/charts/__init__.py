from pareto.helpers.text import labelise

"""
- charts need own version of resource_name because there is intermediate step of chart aggregation (before application of fn::sub)
"""

def resource_name(kwargs):
    return "-".join(["${app_name}",
                     labelise(kwargs["name"]),
                     "${stage_name}"])
    

