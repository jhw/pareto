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
        events=sorted(resp["StackEvents"],
                      key=lambda x: x["Timestamp"])
        table=pd.DataFrame([{"timestamp": event["Timestamp"],
                             "logical_id": event["LogicalResourceId"],
                             "physical_id": event["PhysicalResourceId"],
                             "type": event["ResourceType"],
                             "status": event["ResourceStatus"]}
                            for event in events])
        pd.set_option('display.max_rows', table.shape[0]+1)
        print (table)
    except ClientError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
