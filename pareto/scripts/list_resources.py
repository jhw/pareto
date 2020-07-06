#!/usr/bin/env python

from pareto.scripts import *

def fetch_resources(stackname):
    stacknames=[stack["StackName"]
                for stack in CF.describe_stacks()["Stacks"]
                if stack["StackName"].startswith(stackname)]
    resources=[]
    for stackname in stacknames:
        resources+=CF.describe_stack_resources(StackName=stackname)["StackResources"]
    return resources

if __name__=="__main__":
    try:
        if len(sys.argv) < 2:
            raise RuntimeError("Please enter stage name")
        stagename=sys.argv[1]
        if stagename not in ["dev", "prod"]:
            raise RuntimeError("Stage name is invalid")
        stackname="%s-%s" % (Config["AppName"],
                             stagename)        
        resources=sorted(fetch_resources(stackname),
                         key=lambda x: x["Timestamp"])
        def lookup(event, attr, sz=32):
            return str(event[attr])[:sz] if attr in event else ""
        df=pd.DataFrame([{"timestamp": lookup(resource, "Timestamp"),
                          "stack": lookup(resource, "StackName"),
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
