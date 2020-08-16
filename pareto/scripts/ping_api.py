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
        - name: api
          type: str
        - name: resource
          type: str
        - name: payload
          type: str
        """)
        args=argsparse(sys.argv[1:], argsconfig)
        config=args.pop("config")
        config["globals"]["stage"]=args.pop("stage")
        stackname="%s-%s" % (config["globals"]["app"],
                             config["globals"]["stage"])
        if "apis" not in config["components"]:
            raise RuntimeError("no apis found")
        apis={api["name"]:api
              for api in config["components"]["apis"]}
        if args["api"] not in apis:
            raise RuntimeError("api not found")
        api=apis[args["api"]]
        print (api)
        resources={resource["name"]: resource
                   for resource in api["resources"]}
        if args["resource"] not in resources:
            raise RuntimeError("resource not found")
        resource=resources[args["resource"]]
        print (resource)
    except ClientError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
