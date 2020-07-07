#!/usr/bin/env python

from pareto.scripts import *

"""
- using dict because outputs may duplicated, exported from one nested template and then re- exported from master
"""

def fetch_outputs(stackname):
    outputs={}
    for stack in CF.describe_stacks()["Stacks"]:
        if (stack["StackName"].startswith(stackname) and
            "Outputs" in stack):
            for output in stack["Outputs"]:
                if ("OutputKey" in output and
                    "OutputValue" in output):
                    outputs[output["OutputKey"]]=output["OutputValue"]
    return [(k, v) for k, v in outputs.items()]

if __name__=="__main__":
    try:
        if len(sys.argv) < 2:
            raise RuntimeError("Please enter stage name")
        stagename=sys.argv[1]
        if stagename not in ["dev", "prod"]:
            raise RuntimeError("Stage name is invalid")
        stackname="%s-%s" % (Config["AppName"],
                             stagename)
        outputs=sorted(fetch_outputs(stackname),
                       key=lambda x: x[0])
        for key, value in outputs:
            print ("%s\t\t%s" % (key, value))
    except ClientError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
