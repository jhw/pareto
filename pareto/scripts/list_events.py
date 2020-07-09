#!/usr/bin/env python

from pareto.scripts import *

def fetch_events(stackname):
    stacknames=[stack["StackName"]
                for stack in CF.describe_stacks()["Stacks"]
                if stack["StackName"].startswith(stackname)]
    events=[]
    for stackname in stacknames:
        events+=CF.describe_stack_events(StackName=stackname)["StackEvents"]
    return events

if __name__=="__main__":
    try:
        config=load_config(sys.argv)
        stackname="%s-%s" % (config["globals"]["app"],
                             config["globals"]["stage"])
        events=sorted(fetch_events(stackname),
                      key=lambda x: x["Timestamp"])
        def lookup(event, attr, sz=32):
            return str(event[attr])[:sz] if attr in event else ""
        table=pd.DataFrame([{"timestamp": lookup(event, "Timestamp"),
                             "stack": lookup(event, "StackName"),
                             "logical_id": lookup(event, "LogicalResourceId"),
                             "physical_id": lookup(event, "PhysicalResourceId"),
                             "type": lookup(event, "ResourceType"),
                             "status": lookup(event, "ResourceStatus")}
                            for event in events])
        pd.set_option('display.max_rows', table.shape[0]+1)
        print (table)
    except ClientError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
