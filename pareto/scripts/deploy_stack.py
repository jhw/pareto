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
        
def dump_env(env):
    timestamp=datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
    for tempname, template in env.items():
        tokens=["tmp", "env", timestamp, "%s.yaml" % tempname]
        dirname, filename = "/".join(tokens[:-1]), "/".join(tokens)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(filename, 'w') as f:
            f.write(template.yaml_repr)

def push_templates(config, templates):
    logging.info("pushing templates")
    def push_template(config, tempname, template):
        key="%s-%s/templates/%s.json" % (config["globals"]["app"],
                                         config["globals"]["stage"],
                                         tempname)
        logging.info("pushing %s" % key)
        S3.put_object(Bucket=config["globals"]["bucket"],
                      Key=key,
                      Body=template.json_repr,
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


        
