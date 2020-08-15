#!/usr/bin/env python

from pareto.scripts import *

from pareto.helpers.text import hungarorise

def fetch_outputs(stackname):
    outputs=[]
    for stack in CF.describe_stacks()["Stacks"]:
        if (stack["StackName"].startswith(stackname) and
            "Outputs" in stack):
            outputs+=stack["Outputs"]
    return {output["OutputKey"]: output["OutputValue"]
            for output in outputs}

if __name__=="__main__":
    try:
        init_stdout_logger(logging.INFO)
        argsconfig=yaml.safe_load("""
        - name: config
          type: file
        - name: stage
          type: str
        - name: userpool
          type: str
        """)
        args=argsparse(sys.argv[1:], argsconfig)
        config=args.pop("config")
        config["globals"]["stage"]=args.pop("stage")
        stackname="%s-%s" % (config["globals"]["app"],
                             config["globals"]["stage"])
        outputs=fetch_outputs(stackname)
        if "userpools" not in config["components"]:
            raise RuntimeError("no userpools found")
        userpools={userpool["name"]:userpool
                for userpool in config["components"]["userpools"]}
        if args["userpool"] not in userpools:
            raise RuntimeError("userpool not found")
        userpool=userpools[args["userpool"]]
        key="%sUserPoolId" % hungarorise(userpool["name"])
        if key not in outputs:
            raise RuntimeError("user pool id not found")
        userpoolid=outputs[key]
        resp=CG.list_users(UserPoolId=userpoolid)
        for user in resp["Users"]:
            print (user)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
