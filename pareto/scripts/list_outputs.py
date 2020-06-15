#!/usr/bin/env python

import boto3, sys

Config=dict([tuple(row.split("="))
             for row in open("app.props").read().split("\n")
             if "=" in row])

if __name__=="__main__":
    try:
        if len(sys.argv) < 2:
            raise RuntimeError("Please enter stage name")
        stagename=sys.argv[1]
        if stagename not in ["dev", "prod"]:
            raise RuntimeError("Stage name is invalid")
        cf=boto3.client("cloudformation")
        stackname="%s-%s" % (Config["AppName"],
                             stagename)
        stacks={stack["StackName"]:stack
                for stack in cf.describe_stacks()["Stacks"]}
        if stackname not in stacks:
            raise RuntimeError("%s not found" % stackname)
        outputs=stacks[stackname]["Outputs"]        
        """
        - because pandas truncates column width :-(
        """
        for output in outputs:
            print ("%s\t\t%s" % (output["OutputKey"],
                                 output["OutputValue"]))
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
