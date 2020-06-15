#!/usr/bin/env python

import boto3

import pandas as pd

Config=dict([tuple(row.split("="))
             for row in open("app.props").read().split("\n")
             if "=" in row])

if __name__=="__main__":
    try:
        cf=boto3.client("cloudformation")
        stacks=cf.describe_stacks()["Stacks"]
        df=pd.DataFrame([{"name": stack["StackName"],
                          "status": stack["StackStatus"]}
                         for stack in stacks])
        print (df)
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
