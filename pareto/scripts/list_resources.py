#!/usr/bin/env python

import boto3, sys

import pandas as pd

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
        resp=cf.describe_stack_resources(StackName=stackname)
        resources=sorted(resp["StackResources"],
                         key=lambda x: x["Timestamp"])        
        df=pd.DataFrame([{"timestamp": resource["Timestamp"],
                          "logical_id": resource["LogicalResourceId"],
                          "physical_id": resource["PhysicalResourceId"],
                          "type": resource["ResourceType"],
                          "status": resource["ResourceStatus"]}
                         for resource in resources])
        print (df)
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
