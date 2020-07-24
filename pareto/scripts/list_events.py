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
        argsconfig=yaml.load("""
        - name: config
          type: file
        - name: stage
          type: enum
          options:
          - dev
          - prod
        """, Loader=yaml.FullLoader)
        args=argsparse(sys.argv[1:], argsconfig)
        config=args.pop("config")
        config["globals"]["stage"]=args.pop("stage")
        stackname="%s-%s" % (config["globals"]["app"],
                             config["globals"]["stage"])
        events=sorted(fetch_events(stackname),
                      key=lambda x: x["Timestamp"])
        def lookup(event, attr, sz=32):
            return str(event[attr])[:sz] if attr in event else ""
        df=pd.DataFrame([{"timestamp": lookup(event, "Timestamp"),
                          "stack": lookup(event, "StackName"),
                          "logical_id": lookup(event, "LogicalResourceId"),
                          "physical_id": lookup(event, "PhysicalResourceId"),
                          "type": lookup(event, "ResourceType"),
                          "status": lookup(event, "ResourceStatus")}
                         for event in events])
        pd.set_option('display.max_rows', df.shape[0]+1)
        print (df)
    except ClientError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
