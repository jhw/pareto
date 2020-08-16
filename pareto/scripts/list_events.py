#!/usr/bin/env python

from pareto.scripts import *

from pareto.scripts.helpers.events import Events

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
        def filterfn(event):
            return (args["term"]=="*" or
                    event.matches(args["term"]))
        events=Events.initialise(stackname,
                                 cf=CF,
                                 filterfn=filterfn)
        df=events.table_repr(Attrs)
        pd.set_option('display.max_rows', df.shape[0]+1)
        print (df)
    except ClientError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
