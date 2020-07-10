#!/usr/bin/env python

from pareto.scripts import *

def fetch_events(stackname):
    stacknames=[stack["StackName"]
                for stack in CF.describe_stacks()["Stacks"]
                if stack["StackName"].startswith(stackname)]
    events=[]
    for stackname in stacknames:
        try:
            events+=CF.describe_stack_events(StackName=stackname)["StackEvents"]
        except ValidationError:
            pass
    return events

if __name__=="__main__":
    try:
        config=load_config(sys.argv)
        stackname="%s-%s" % (config["globals"]["app"],
                             config["globals"]["stage"])
        events=sorted([event for event in fetch_events(stackname)
                       if ("FAIL" in event["ResourceStatus"] and
                           event["ResourceStatusReason"]!="Resource creation cancelled")],                      
                      key=lambda x: x["Timestamp"])
        def lookup(event, attr):
            return event[attr] if attr in event else ""
        for event in events:
            print ("%s\t%s\t%s\t%s\t%s" % (lookup(event, "Timestamp"),
                                           lookup(event, "StackName"),
                                           lookup(event, "LogicalResourceId"),
                                           lookup(event, "ResourceType"),
                                           lookup(event, "ResourceStatusReason")))
    except ClientError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
