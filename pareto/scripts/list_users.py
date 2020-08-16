#!/usr/bin/env python

from pareto.scripts import *

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
        """)
        args=argsparse(sys.argv[1:], argsconfig)
        config=args.pop("config")
        config["globals"]["stage"]=args.pop("stage")
        stackname="%s-%s" % (config["globals"]["app"],
                             config["globals"]["stage"])
        if "userpools" not in config["components"]:
            raise RuntimeError("no userpools found")
        userpools={userpool["name"]:userpool
                for userpool in config["components"]["userpools"]}
        if args["userpool"] not in userpools:
            raise RuntimeError("userpool not found")
        userpool=userpools[args["userpool"]]
        outputs=Outputs.initialise(stackname, CF)
        userpoolid=outputs.lookup("%s-user-pool-id" % userpool["name"]) 
        resp=CG.list_users(UserPoolId=userpoolid)
        print (yaml.safe_dump(resp["Users"],
                              default_flow_style=False))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
