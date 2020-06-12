#!/usr/bin/env python

from pareto.components.stack import synth_stack

import yaml

Config=dict([tuple(row.split("="))
             for row in open("app.props").read().split("\n")
             if "=" in row])

if __name__=="__main__":
    try:
        import sys, os
        if len(sys.argv) < 3:
            raise RuntimeError("Please enter stack file, stage name")
        stackfile, stagename = sys.argv[1:3]
        if stagename not in ["dev", "prod"]:
            raise RuntimeError("Stage name is invalid")
        if not stackfile.endswith(".yaml"):
            raise RuntimeError("Stack must be a yaml file")
        if not os.path.exists(stackfile):
            raise RuntimeError("Stack file does not exist")
        with open(stackfile, 'r') as f:
            config=yaml.load(f.read(),
                             Loader=yaml.FullLoader)
        config["app"]=Config["AppName"]
        config["region"]=Config["AWSRegion"]
        config["stage"]=stagename
        stack=synth_stack(config)
        with open("template-%s.yaml" % stagename, 'w') as f:
            f.write(yaml.safe_dump(stack,
                                   default_flow_style=False))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
