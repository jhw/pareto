#!/usr/bin/env python

from pareto.scripts import *

"""
- you don't technically need the stage name here but hey
"""

if __name__=="__main__":
    try:
        config=load_config(sys.argv)
        paginator=S3.get_paginator("list_objects_v2")
        pages=paginator.paginate(Bucket=config["globals"]["bucket"],
                                 Prefix=config["globals"]["app"])
        count=0
        for struct in pages:
            if "Contents" in struct:
                for obj in struct["Contents"]:                    
                    print (obj["Key"])
                    S3.delete_object(Bucket=config["globals"]["bucket"],
                                     Key=obj["Key"])                    
                    count+=1
        print ()
        print ("%i files deleted" % count)
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
