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
        resp=CF.describe_stack_events(StackName=stackname)
        events=sorted([event for event in resp["StackEvents"]
                       if ("FAIL" in event["ResourceStatus"] and
                           event["ResourceStatusReason"]!="Resource creation cancelled")],                      
                      key=lambda x: x["Timestamp"])
        """
        - because pandas truncates column width :-(
        """
        for event in events:
            print ("%s\t\t%s\t\t%s\t\t%s" % (event["Timestamp"],
                                             event["LogicalResourceId"],
                                             event["ResourceType"],
                                             event["ResourceStatusReason"]))
    except ClientError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
