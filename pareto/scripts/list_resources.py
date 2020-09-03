#!/usr/bin/env python

from pareto.scripts import *

from pareto.scripts.helpers.resources import Resources

Attrs=yaml.safe_load("""
- Timestamp
# - StackName
- LogicalResourceId
- PhysicalResourceId
- ResourceType
- ResourceStatus
""")

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
        def filterfn(resource):
            return (args["term"] in ["*", ""] or
                    resource.matches(args["term"]))
        resources=Resources.initialise(stackname,
                                       cf=boto3.client("cloudformation"),
                                       filterfn=filterfn)
        df=resources.table_repr(Attrs)
        pd.set_option('display.max_rows', df.shape[0]+1)
        print (df)
    except ClientError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
