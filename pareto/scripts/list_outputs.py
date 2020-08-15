#!/usr/bin/env python

from pareto.scripts import *

def fetch_outputs(stackname):
    outputs=[]
    for stack in CF.describe_stacks()["Stacks"]:
        if (stack["StackName"].startswith(stackname) and
            "Outputs" in stack):
            outputs+=stack["Outputs"]
    return outputs

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
        """
        - assuming every Output is guaranteed to have OutputKey, OutputValue
        """
        outputs=sorted(fetch_outputs(stackname),
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
