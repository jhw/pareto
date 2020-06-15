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
        resp=CF.describe_stack_resources(StackName=stackname)
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
