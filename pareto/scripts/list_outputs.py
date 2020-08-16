#!/usr/bin/env python

from pareto.scripts import *

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
        - name: verbose
          type: bool
        """)
        args=argsparse(sys.argv[1:], argsconfig)
        config=args.pop("config")
        config["globals"]["stage"]=args.pop("stage")
        stackname="%s-%s" % (config["globals"]["app"],
                             config["globals"]["stage"])
        def filterfn(k, v):
            return (args["verbose"] or
                    re.search("arn", v, re.I)==None)
        outputs=Outputs.initialise(stackname,
                                   cf=CF,
                                   filterfn=filterfn)
        print (outputs.table_repr)
    except ClientError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
