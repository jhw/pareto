#!/usr/bin/env python

from pareto.scripts import *

if __name__=="__main__":
    try:
        stacks=CF.describe_stacks()["Stacks"]
        df=pd.DataFrame([{"name": stack["StackName"],
                          "status": stack["StackStatus"]}
                         for stack in stacks])
        print (df)
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
