#!/usr/bin/env python

from pareto.scripts import *

def fetch_resources(stackname):
    stacknames=[stack["StackName"]
                for stack in CF.describe_stacks()["Stacks"]
                if stack["StackName"].startswith(stackname)]
    resources=[]
    for stackname in stacknames:
        try:
            resources+=CF.describe_stack_resources(StackName=stackname)["StackResources"]
        except ValidationError:
            pass
    return resources

if __name__=="__main__":
    try:
        argsconfig=yaml.safe_load("""
        - name: config
          type: file
        - name: stage
          type: enum
          options:
          - dev
          - prod
        - name: term
          type: str
        """)
        args=argsparse(sys.argv[1:], argsconfig)
        config=args.pop("config")
        config["globals"]["stage"]=args.pop("stage")
        stackname="%s-%s" % (config["globals"]["app"],
                             config["globals"]["stage"])
        resources=sorted(fetch_resources(stackname),
                         key=lambda x: x["Timestamp"])
        def lookup(resource, attr, sz=32):
            return str(resource[attr])[:sz] if attr in resource else ""
        def is_valid(resource, term):
            for attr in ["StackName",
                         "LogicalResourceId",
                         "PhysicalResourceId",
                         "ResourceType"]:
                if re.search(term, lookup(resource, attr), re.I):
                    return True
            return False
        df=pd.DataFrame([{"timestamp": lookup(resource, "Timestamp"),
                          "stack": lookup(resource, "StackName"),
                          "logical_id": lookup(resource, "LogicalResourceId"),
                          "physical_id": lookup(resource, "PhysicalResourceId"),
                          "type": lookup(resource, "ResourceType"),
                          "status": lookup(resource, "ResourceStatus")}
                         for resource in resources
                         if (args["term"]=="*" or
                             is_valid(resource, args["term"]))])
        pd.set_option('display.max_rows', df.shape[0]+1)
        print (df)
    except ClientError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
