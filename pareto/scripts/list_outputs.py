#!/usr/bin/env python

from pareto.scripts import *

def fetch_outputs(stackname):
    outputs=[]
    for stack in CF.describe_stacks()["Stacks"]:
        if (stack["StackName"].startswith(stackname) and
            "Outputs" in stack):
            outputs+=stack["Outputs"]
    return outputs

if __name__=="__main__":
    try:
        if len(sys.argv) < 2:
            raise RuntimeError("Please enter stage name")
        stagename=sys.argv[1]
        if stagename not in ["dev", "prod"]:
            raise RuntimeError("Stage name is invalid")
        stackname="%s-%s" % (Config["AppName"],
                             stagename)
        """
        - assuming every Output is guaranteed to have OutputKey, OutputValue
        """
        outputs=sorted(fetch_outputs(stackname),
                       key=lambda x: x["OutputKey"])
        for output in outputs:
            print ("%s\t\t%s" % (output["OutputKey"],
                                 output["OutputValue"]))
    except ClientError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
