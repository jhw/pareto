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
        def lookup(resource, attr):
            return resource[attr] if attr in resource else ""
        df=pd.DataFrame([{"timestamp": lookup(resource, "Timestamp"),
                          "logical_id": lookup(resource, "LogicalResourceId"),
                          "physical_id": lookup(resource, "PhysicalResourceId"),
                          "type": lookup(resource, "ResourceType"),
                          "status": lookup(resource, "ResourceStatus")}
                         for resource in resources])
        print (df)
    except ClientError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
