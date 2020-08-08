#!/usr/bin/env python

from pareto.scripts import *

from pareto.staging.lambdas import *
from pareto.staging.layers import *

from pareto.env import synth_env

def init_region(config):
    region=boto3.session.Session().region_name
    if region in ['', None]:
        raise RuntimeError("region is not set in AWS profile")
    config["globals"]["region"]=region

@assert_actions
def add_lambda_staging(config):
    logging.info("adding lambda staging")
    def add_staging(action, commits):
        groups, latest = commits.grouped, commits.latest
        staging={"bucket": config["globals"]["bucket"]}
        if "commit" in action: 
            if action["commit"] not in groups[action["name"]]:
                raise RuntimeError("commit %s not found for %s" % (action["commit"], action["name"]))
            staging["key"]=str(groups[action["name"]][action["commit"]])
        else:
            if action["name"] not in latest:
                raise RuntimeError("no deployables found for %s" % action["name"])
            staging["key"]=str(latest[action["name"]])
        action.setdefault("staging", {})
        action["staging"]["lambda"]=staging    
    commits=LambdaCommits(config=config, s3=S3)
    for action in config["components"]["actions"]:
       add_staging(action, commits)

@assert_actions
def add_layer_staging(config):
    logging.info("adding layer staging")
    def filter_staged(config, action, packages):
        staged=[]
        for layerkwargs in action["layers"]:
            package=LayerPackage.create(config, **layerkwargs)
            if not packages.exists(package):
                raise RuntimeError("%s does not exist" % package)
            staged.append(package)
        return staged
    def assert_unique_versions(action, packages):        
        names=[package["name"]
               for package in packages]
        unames=list(set(names))
        if len(names)!=len(unames):
            raise RuntimeError("%s has multiple versions of the same package" % action["name"])
    packages=LayerPackages(config=config, s3=S3)
    for action in config["components"]["actions"]:
        if "layers" not in action:
            continue
        staged=filter_staged(config, action, packages)
        assert_unique_versions(action, staged)
        action.setdefault("staging", {})
        action["staging"]["layer"]=staged
        
"""
- remember this checks resource ids (1st arg to fn:getatt) and not attribute names (2nd arg)
- hence doesn't cover `Outputs.XXX`
"""
        
def check_refs(templates):
    logging.info("checking template refs")
    def filter_resource_ids(template):
        ids=[]
        for attr in ["Resources", "Parameters"]:
            if attr in template:
                ids+=template[attr].keys()
        return ids
    def is_new_ref(key, element, refs):
        return (key=="Ref" and
                type(element)==str and
                element not in refs)
    def is_new_getatt(key, element, refs):
        return (key=="Fn::GetAtt" and
                type(element)==list and
                type(element[0])==str and
                element[0] not in refs)
    def filter_refs(element, refs):
        if isinstance(element, list):
            for subelement in element:
                filter_refs(subelement, refs)
        elif isinstance(element, dict):
            for key, subelement in element.items():
                if is_new_ref(key, subelement, refs):
                    # print ("ref: %s" % subelement)
                    refs.append(subelement)
                elif is_new_getatt(key, subelement, refs):
                    # print ("getatt: %s" % subelement[0])
                    refs.append(subelement[0])
                else:
                    filter_refs(subelement, refs)
        else:
            pass
    def check_refs(tempname, template):
        resourceids=filter_resource_ids(template)
        refs=[]
        filter_refs(template, refs)
        for ref in refs:
            if ref not in resourceids:
                raise RuntimeError("bad reference to %s in %s template" % (ref, tempname))
    for tempname, template in templates.items():
        check_refs(tempname, template)
        
"""
- some CF methods, notably apigw ones related to HTTP headers, *require* single- quote enclosed strings
- both json.dumps and yaml.safe_dump mess this up
- json.dumps can be fixed with custom encoder (see push_templates)
- but hacking pyyaml is more complex
- could use https://pypi.org/project/ruamel.yaml/ but not convinced want to deprecate pyyaml at this stage, esp as not required here - the yaml dump is just for debugging
- so simpler to add unescape_single_quotes() for consistency with custom json encoder
- https://stackoverflow.com/questions/37094170/a-single-string-in-single-quotes-with-pyyaml
"""
    
def dump_env(env):
    def unescape_single_quotes(text):
        class Counter:
            def __init__(self):
                self.value=0
            def increment(self):
                self.value+=1
        def count(fn):
            counter=Counter()
            def wrapped(match):
                resp=fn(match, counter)
                counter.increment()
                return resp
            return wrapped
        @count
        def matcher(match, counter):
            return "\"'" if 0==counter.value % 2 else "'\""
        return re.sub("'''", matcher, text)
    yaml.Dumper.ignore_aliases=lambda *args : True
    timestamp=datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
    for tempname, template in env.items():
        tokens=["tmp", "env", timestamp, "%s.yaml" % tempname]
        dirname, filename = "/".join(tokens[:-1]), "/".join(tokens)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(filename, 'w') as f:
            f.write(unescape_single_quotes(yaml.dump(dict(template), # remove Template class
                                                     default_flow_style=False)))

def push_templates(config, templates):
    logging.info("pushing templates")
    """
    - encoder to avoid escaping single quotes
    - for some fields, particularly apigw http header- like fields, CF *requires* non- escaped single quotes
    """
    class CFSingleQuoteEncoder(json.JSONEncoder):
        def default(self, obj):
            if (isinstance(obj, str) and
                "'" in obj):
                return obj
            return json.JSONEncoder.default(self, obj)
    def push_template(config, tempname, template):
        key="%s-%s/templates/%s.json" % (config["globals"]["app"],
                                         config["globals"]["stage"],
                                         tempname)
        logging.info("pushing %s" % key)
        body=json.dumps(template,
                        cls=CFSingleQuoteEncoder).encode("utf-8")
        S3.put_object(Bucket=config["globals"]["bucket"],
                      Key=key,
                      Body=body,
                      ContentType='application/json')
    for tempname, template in templates.items():
        if tempname=="master":
            continue
        push_template(config, tempname, template)

def deploy_env(config, template):
    logging.info("deploying stack")
    def stack_exists(stackname):
        stacknames=[stack["StackName"]
                    for stack in CF.describe_stacks()["Stacks"]]
        return stackname in stacknames
    stackname="%s-%s" % (config["globals"]["app"],
                         config["globals"]["stage"])
    action="update" if stack_exists(stackname) else "create"
    fn=getattr(CF, "%s_stack" % action)
    fn(StackName=stackname,
       TemplateBody=json.dumps(template),
       Capabilities=["CAPABILITY_IAM"])
    waiter=CF.get_waiter("stack_%s_complete" % action)
    waiter.wait(StackName=stackname)
        
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
        - name: live
          type: bool
        """)
        args=argsparse(sys.argv[1:], argsconfig)
        config=args.pop("config")
        config["globals"]["stage"]=args.pop("stage")
        init_region(config)    
        validate_bucket(config)
        add_lambda_staging(config)
        add_layer_staging(config)
        env=synth_env(config)
        check_refs(env)
        dump_env(env)
        push_templates(config, env)
        if args["live"]:
            deploy_env(config, env["master"])
    except ClientError as error:
        logging.error(error)                      
    except WaiterError as error:
        logging.error(error)                      
    except RuntimeError as error:
        logging.error(error)                      


        
