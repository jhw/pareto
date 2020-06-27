#!/usr/bin/env python

from pareto.scripts import *

if __name__=="__main__":
    try:
        if len(sys.argv) < 2:
            raise RuntimeError("Please enter stage name")
        stagename=sys.argv[1]
        if stagename not in ["dev", "prod"]:
            raise RuntimeError("Stage name is invalid")
        stackname="%s-%s" % (Config["AppName"],
                             stagename)
        stacks={stack["StackName"]:stack
                for stack in CF.describe_stacks()["Stacks"]}
        if stackname not in stacks:
            raise RuntimeError("%s not found" % stackname)
        outputs=stacks[stackname]["Outputs"]        
        """
        - because pandas truncates column width :-(
        """
        def lookup(output, attr):
            return output[attr] if attr in output else ""
        for output in outputs:
            print ("%s\t\t%s" % (lookup(output, "OutputKey"),
                                 lookup(output, "OutputValue")))
    except ClientError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
