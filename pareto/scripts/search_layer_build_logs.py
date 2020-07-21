#!/usr/bin/env python

"""
- doesn't use logging as logs output already includes timestamps
"""

from pareto.scripts import *

from pareto.staging.layers import *

if __name__=="__main__":
    try:
        argsconfig=yaml.load("""
        - name: config
          type: file
        - name: package
          type: str
        - name: window
          type: int
        - name: query
          type: str
        """, Loader=yaml.FullLoader)
        args=argsparse(sys.argv[1:], argsconfig)
        config=args.pop("config")
        package=LayerPackage.parse(args.pop("package"))
        loggroupname="/aws/codebuild/%s" % layer_project_name(config,
                                                              package)
        starttime=int(1000*(time.time()-args["window"]))                
        kwargs={"logGroupName": loggroupname,
                "startTime": starttime,
                "interleaved": True}
        if args["query"]!="*":
            kwargs["filterPattern"]=args["query"]
        events=Logs.filter_log_events(**kwargs)["events"]        
        for event in sorted(events,
                            key=lambda x: x["timestamp"]):
            print (re.sub("\\r|\\n", "", event["message"]))
    except ClientError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % str(error))