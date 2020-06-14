#!/usr/bin/env python

import yaml

Config=dict([tuple(row.split("="))
             for row in open("app.props").read().split("\n")
             if "=" in row])

if __name__=="__main__":
    try:
        import sys, os
        if len(sys.argv) < 2:
            raise RuntimeError("Please enter stage name")
        stagename=sys.argv[1]
        if stagename not in ["dev", "prod"]:
            raise RuntimeError("Stage name is invalid")
        stackfile="tmp/template-%s.yaml" % stagename
        if not os.path.exists(stackfile):
            raise RuntimeError("Stack file does not exist")
        with open(stackfile, 'r') as f:
            stack=yaml.load(f.read(),
                            Loader=yaml.FullLoader)
        print (stack)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
