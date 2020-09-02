#!/usr/bin/env python

from pareto.scripts import *

from pareto.helpers.text import hungarorise

def get_token(cg, resource, outputs, args):
    userpoolid=outputs.lookup("%s-user-pool-id" % resource["userpool"])
    userpoolclientid=outputs.lookup("%s-user-pool-client-id" % resource["userpool"])
    resp=cg.admin_initiate_auth(UserPoolId=userpoolid,
                                ClientId=userpoolclientid,
                                AuthFlow='ADMIN_NO_SRP_AUTH',
                                AuthParameters={"USERNAME": args["email"],
                                                "PASSWORD": args["password"]})
    return resp["AuthenticationResult"]["IdToken"]

def validate_get_payload(fn):
    def is_form_urlencoded(payload):
        return re.search("^(\\w+\\=\\w+\\&)*\\w+\\=\\w+$", payload)!=None
    def wrapped(url, payload, token):
        if is_form_urlencoded(payload):                
            return fn(url="%s?%s" % (url, payload),
                      token=token)
        else:
            raise RuntimeError("GET payload is invalid")
    return wrapped

def init_get_headers(fn):
    def wrapped(url, token):
        headers={}
        if token:
            headers["Authorization"]="Bearer %s" % token
        return fn(url=url,
                  headers=headers)
    return wrapped

@validate_get_payload
@init_get_headers
def http_get(url, headers):
    return requests.get(url,
                        headers=headers)

def validate_post_payload(fn):
    def is_json(payload):
        try:
            json.loads(payload)
            return True
        except:
            return False
    def wrapped(url, payload, token):
        if is_json(payload):                
            return fn(url=url,
                      payload=payload,
                      token=token)
        else:
            raise RuntimeError("POST payload is invalid")
    return wrapped

def init_post_headers(fn):
    def wrapped(url, payload, token):
        headers={"Content-Type": "application/json"}
        if token:
            headers["Authorization"]="Bearer %s" % token
        return fn(url=url,
                  headers=headers,
                  payload=payload)
    return wrapped

@validate_post_payload
@init_post_headers
def http_post(url, headers, payload):
    return requests.post(url,
                         headers=headers,
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
        cf=boto3.client("cloudformation")
        outputs=Outputs.initialise(stackname, cf)
        url=outputs.lookup("%s-%s-url" % (api["name"],
                                          resource["name"]))
        cg=boto3.client("cognito-idp")
        token=get_token(cg, resource, outputs, args) if "userpool" in resource else None
        if token:
            print ("Token => %s" % token)
            print()
        httpfn=eval("http_%s" % resource["method"].lower())
        resp=httpfn(url=url,
                    payload=args["payload"],
                    token=token)
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
