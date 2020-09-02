#!/usr/bin/env python

"""
- doesn't use logging as logs output already includes timestamps
"""

from pareto.scripts import *

from pareto.scripts.build_layer import layer_project_name

if __name__=="__main__":
    try:
        argsconfig=yaml.safe_load("""
        - name: config
          type: file
        - name: layer
          type: str
        - name: window
          type: int
        - name: query
          type: str
        """)
        args=argsparse(sys.argv[1:], argsconfig)
        config=args.pop("config")
        layer={"name": args["layer"]}
        loggroupname="/aws/codebuild/%s" % layer_project_name(config,
                                                              layer)
        starttime=int(1000*(time.time()-args["window"]))                
        kwargs={"logGroupName": loggroupname,
                "startTime": starttime,
                "interleaved": True}
        if args["query"]!="*":
            kwargs["filterPattern"]=args["query"]
        logs=boto3.client("logs")
        events=logs.filter_log_events(**kwargs)["events"]        
        for event in sorted(events,
                            key=lambda x: x["timestamp"]):
            print (re.sub("\\r|\\n", "", event["message"]))
    except ClientError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
