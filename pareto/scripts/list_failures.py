#!/usr/bin/env python

from pareto.scripts import *

from pareto.scripts.helpers.events import Events

Attrs=yaml.safe_load("""
- Timestamp
- StackName
- LogicalResourceId
- ResourceType
- ResourceStatusReason
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
        """)
        args=argsparse(sys.argv[1:], argsconfig)
        config=args.pop("config")
        config["globals"]["stage"]=args.pop("stage")
        stackname="%s-%s" % (config["globals"]["app"],
                             config["globals"]["stage"])
        def filterfn(event):
            return event.matches("fail")
        events=Events.initialise(stackname,
                                 cf=boto3.client("cloudformation"),
                                 filterfn=filterfn)
        formatstr=" :: ".join(["%s" for i in range(len(Attrs))])
        for event in events:            
            print (formatstr % tuple([event.lookup(attr)
                                      for attr in Attrs]))
    except ClientError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
