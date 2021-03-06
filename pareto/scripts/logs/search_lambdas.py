#!/usr/bin/env python

"""
- doesn't use logging as logs output already includes timestamps
"""

from pareto.scripts import *

from pareto.helpers.text import hyphenate

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
        - name: lambda
          type: str
        - name: window
          type: int
        - name: query
          type: str
        """)
        args=argsparse(sys.argv[1:], argsconfig)
        config=args.pop("config")
        lambdanames=[hyphenate(dirname)
                     for dirname in os.listdir(config["globals"]["app"])]
        if args["lambda"] not in lambdanames:
            raise RuntimeError("lambda %s not found" % args["lambda"])
        loggroupname="/aws/lambda/%s-%s-%s" % (config["globals"]["app"],
                                               args["lambda"],
                                               args["stage"])
        starttime=int(1000*(time.time()-args["window"]))                
        kwargs={"logGroupName": loggroupname,
                "startTime": starttime,
                "interleaved": True}
        if args["query"] not in ["*", ""]:
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
