#!/usr/bin/env python

from pareto.scripts import *

if __name__=="__main__":
    try:
        paginator=Logs.get_paginator('describe_log_groups')
        for page in paginator.paginate():
            for group in page["logGroups"]:
                print (group["logGroupName"])
    except ClientError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % str(error))


