#!/usr/bin/env python

from pareto.scripts import *

if __name__=="__main__":
    try:
        argsconfig=yaml.safe_load("""
        - name: prefix
          type: str
        """)
        args=argsparse(sys.argv[1:], argsconfig)
        for group in Logs.describe_log_groups(logGroupNamePrefix=args["prefix"])["logGroups"]:
            print ("deleting %s" % group["logGroupName"])
            Logs.delete_log_group(logGroupName=group["logGroupName"])
    except ClientError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % str(error))


