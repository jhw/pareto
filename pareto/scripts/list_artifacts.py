#!/usr/bin/env python

from pareto.scripts import *

"""
- you don't technically need the stage name here but hey
"""

if __name__=="__main__":
    try:
        init_stdout_logger(logging.INFO)
        argsconfig=yaml.load("""
        - name: config
          type: file
        """, Loader=yaml.FullLoader)
        args=argsparse(sys.argv[1:], argsconfig)
        config=args.pop("config")
        paginator=S3.get_paginator("list_objects_v2")
        pages=paginator.paginate(Bucket=config["globals"]["bucket"],
                                 Prefix=config["globals"]["app"])
        count=0
        for struct in pages:
            if "Contents" in struct:
                for obj in struct["Contents"]:
                    print (obj["Key"])
                    count+=1
        print ()
        print ("%i files" % count)
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
