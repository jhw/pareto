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
        outputs=sorted([{"OutputKey": k,
                         "OutputValue": v}
                        for k, v in Outputs.initialise(stackname, CF).items()],
                       key=lambda x: x["OutputKey"])
        def format_string(text, n=32):
            return text+"".join([' '
                                 for i in range(n-len(text))]) if len(text) < n else text[:n]            
        for output in outputs:
            if (not args["verbose"] and
                re.search("arn", output["OutputKey"], re.I)!=None):
                continue
            print ("%s\t%s" % (format_string(output["OutputKey"]),
                               output["OutputValue"]))
    except ClientError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
