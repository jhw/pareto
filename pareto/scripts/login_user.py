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
          type: enum
          options:
          - dev
          - prod
        - name: userpool
          type: str
        - name: email
          type: email
        - name: password
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
        userpoolkey="%sUserPoolId" % hungarorise(userpool["name"])
        if userpoolkey not in outputs:
            raise RuntimeError("user pool id not found")            
        userpoolid=outputs[userpoolkey]
        userpoolclientkey="%sUserPoolClientId" % hungarorise(userpool["name"])
        if userpoolclientkey not in outputs:
            raise RuntimeError("user pool client id not found")
        userpoolclientid=outputs[userpoolclientkey]
        resp=CG.admin_initiate_auth(UserPoolId=userpoolid,
                                    ClientId=userpoolclientid,
                                    AuthFlow='ADMIN_NO_SRP_AUTH',
                                    AuthParameters={"USERNAME": args["email"],
                                                    "PASSWORD": args["password"]})
        print (yaml.safe_dump(resp, default_flow_style=False))
    except ClientError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
