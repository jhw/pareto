#!/usr/bin/env python

from pareto.scripts import *

from pareto.helpers.text import hungarorise

def validate_form_urlencoded(fn):
    def is_form_urlencoded(payload):
        return re.search("^(\\w+\\=\\w+\\&)*\\w+\\=\\w+$", payload)!=None
    def wrapped(url, payload):
        if is_form_urlencoded(payload):                
            return fn(url, payload)
        else:
            raise RuntimeError("GET payload is invalid")
    return wrapped

@validate_form_urlencoded
def http_get(url, payload):
    return requests.get("%s?%s" % (url, payload))

def validate_json(fn):
    def is_json(payload):
        try:
            json.loads(payload)
            return True
        except:
            return False
    def wrapped(url, payload):
        if is_json(payload):                
            return fn(url, payload)
        else:
            raise RuntimeError("POST payload is invalid")
    return wrapped

@validate_json
def http_post(url, payload):
    return requests.post(url,
                         headers={"Content-Type": "application/json"},
                         data=payload)
    
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
        resources={resource["name"]: resource
                   for resource in api["resources"]}
        if args["resource"] not in resources:
            raise RuntimeError("resource not found")
        resource=resources[args["resource"]]
        outputs=Outputs.initialise(stackname, CF)
        url=outputs.lookup("%s-%s-url" % (api["name"],
                                          resource["name"]))
        httpfn=eval("http_%s" % resource["method"].lower())
        resp=httpfn(url, args["payload"])
        for attr in ["status_code",
                     "headers",
                     "text"]:
            print ("%s => %s" % (hungarorise(attr),
                                 getattr(resp, attr)))
            print ()
    except ClientError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
