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
        - name: bucket
          type: str
        """)
        args=argsparse(sys.argv[1:], argsconfig)
        config=args.pop("config")
        config["globals"]["stage"]=args.pop("stage")
        stackname="%s-%s" % (config["globals"]["app"],
                             config["globals"]["stage"])
        if "buckets" not in config["components"]:
            raise RuntimeError("no buckets found")
        buckets={bucket["name"]:bucket
                 for bucket in config["components"]["buckets"]}
        if args["bucket"] not in buckets:
            raise RuntimeError("bucket not found")
        bucket=buckets[args["bucket"]]
        if "website" not in bucket:
            raise RuntimeError("bucket is not a website")
        bucketname="%s-%s-%s" % (config["globals"]["app"],
                                 bucket["name"],
                                 config["globals"]["stage"])
        print (S3.put_object(Bucket=bucketname,
                             Key="index.json",
                             Body=json.dumps({"hello": "world"}),
                             ContentType="application/json"))
    except ClientError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
