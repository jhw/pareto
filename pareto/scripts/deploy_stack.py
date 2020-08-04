#!/usr/bin/env python

from pareto.scripts import *

from pareto.staging.lambdas import *
from pareto.staging.layers import *

from pareto.env import synth_env

"""
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cloudformation-limits.html
"""

Metrics={"resources": (lambda x: (len(x["Resources"]) if "Resources" in x else 0)/200),
         "outputs": (lambda x: (len(x["Outputs"]) if "Outputs" in x else 0)/60),
         "template_size": (lambda x: (len(json.dumps(x))/51200))}

def init_region(config):
    region=boto3.session.Session().region_name
    if region in ['', None]:
        raise RuntimeError("region is not set in AWS profile")
    config["globals"]["region"]=region

def add_lambda_staging(config):
    logging.info("adding lambda staging")
    def add_staging(component, commits):
        groups, latest = commits.grouped, commits.latest
        staging={"bucket": config["globals"]["bucket"]}
        if "commit" in component: 
            if component["commit"] not in groups[component["name"]]:
                raise RuntimeError("commit %s not found for %s" % (component["commit"], component["name"]))
            staging["key"]=str(groups[component["name"]][component["commit"]])
        else:
            if component["name"] not in latest:
                raise RuntimeError("no deployables found for %s" % component["name"])
            staging["key"]=str(latest[component["name"]])
        component.setdefault("staging", {})
        component["staging"]["lambda"]=staging    
    commits=LambdaCommits(config=config, s3=S3)
    for component in config["components"]["actions"]:
       add_staging(component, commits)

def add_layer_staging(config):
    logging.info("adding layer staging")
    def filter_staged(config, component, packages):
        staged=[]
        for layerkwargs in component["layers"]:
            package=LayerPackage.create(config, **layerkwargs)
            if not packages.exists(package):
                raise RuntimeError("%s does not exist" % package)
            staged.append(package)
        return staged
    def assert_unique_versions(component, packages):        
        names=[package["name"]
               for package in packages]
        unames=list(set(names))
        if len(names)!=len(unames):
            raise RuntimeError("%s has multiple versions of the same package" % component["name"])
    packages=LayerPackages(config=config, s3=S3)
    for component in config["components"]["actions"]:
        if "layers" not in component:
            continue
        staged=filter_staged(config, component, packages)
        assert_unique_versions(component, staged)
        component.setdefault("staging", {})
        component["staging"]["layer"]=staged
        
"""
- cloudformation will check this for you early in deployment process
- but still better to have local version to get early warning I think
- in particular is effective at checking references to logical id which may have been incorrectly coded within components
"""
        
def check_refs(templates):
    logging.info("checking template refs")
    class Refs(list):
        def __init__(self, items=[]):
            list.__init__(self, items)
        def add(self, value):
            self.append(value.split(".")[0]) # remove `.Outputs`
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
                    refs.add(subelement)
                elif is_new_getatt(key, subelement, refs):
                    # print ("getatt: %s" % subelement[0])
                    refs.add(subelement[0])
                else:
                    filter_refs(subelement, refs)
        else:
            pass
    def check_refs(tempname, template):
        resourceids=filter_resource_ids(template)
        refs=Refs()
        filter_refs(template, refs)
        for ref in refs:
            if ref not in resourceids:
                raise RuntimeError("bad reference to %s in %s template" % (ref, tempname))
    for tempname, template in templates.items():
        check_refs(tempname, template)
        
def check_metrics(templates, metrics=Metrics):
    logging.info("checking template metrics")
    def calc_metrics(tempname, template, metrics):
        outputs={"name": tempname}
        outputs.update({metrickey: metricfn(template)
                        for metrickey, metricfn in metrics.items()})
        return outputs
    def validate_metrics(metrics, limit=0.9):
        for row in metrics:
            for attr in row.keys():
                if (type(row[attr])==float and
                    row[attr] > limit):
                    raise RuntimeError("%s %s exceeds limit" % (row["name"],
                                                                attr))
    metrics=[calc_metrics(tempname, template, metrics)
             for tempname, template in templates.items()]
    print ("\n%s\n" % pd.DataFrame(metrics))
    validate_metrics(metrics)

def dump_env(env):
    yaml.SafeDumper.ignore_aliases=lambda *args: True
    timestamp=datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
    for tempname, template in env.items():
        tokens=["tmp", "env", timestamp, "%s.yaml" % tempname]
        dirname, filename = "/".join(tokens[:-1]), "/".join(tokens)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(filename, 'w') as f:
            f.write(yaml.safe_dump(template,
                                   default_flow_style=False))

def push_templates(config, templates):
    logging.info("pushing templates")
    def push_template(config, tempname, template):
        key="%s-%s/templates/%s.json" % (config["globals"]["app"],
                                         config["globals"]["stage"],
                                         tempname)
        logging.info("pushing %s" % key)
        body=json.dumps(template).encode("utf-8")
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
        argsconfig=yaml.load("""
        - name: config
          type: file
        - name: stage
          type: enum
          options:
          - dev
          - prod
        - name: live
          type: bool
        """, Loader=yaml.FullLoader)
        args=argsparse(sys.argv[1:], argsconfig)
        config=args.pop("config")
        config["globals"]["stage"]=args.pop("stage")
        init_region(config)    
        validate_bucket(config)
        add_lambda_staging(config)
        add_layer_staging(config)
        env=synth_env(config)
        check_refs(env)
        check_metrics(env)
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


        
