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
        if "userpools" not in config["components"]:
            raise RuntimeError("no userpools found")
        userpools={userpool["name"]:userpool
                for userpool in config["components"]["userpools"]}
        if args["userpool"] not in userpools:
            raise RuntimeError("userpool not found")
        userpool=userpools[args["userpool"]]
        outputs=Outputs.initialise(stackname, boto3.client("cloudformation"))
        userpoolid=outputs.lookup("%s-user-pool-id" % userpool["name"])
        userpoolclientid=outputs.lookup("%s-user-pool-admin-client-id" % userpool["name"])
        cg=boto3.client("cognito-idp")
        resp=cg.sign_up(ClientId=userpoolclientid,
                        Username=args["email"],
                        Password=args["password"])
        print (yaml.safe_dump(resp, default_flow_style=False))
        resp=cg.admin_confirm_sign_up(UserPoolId=userpoolid,
                                      Username=args["email"])
        print (yaml.safe_dump(resp, default_flow_style=False))
    except ClientError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
