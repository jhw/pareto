#!/usr/bin/env python

from pareto.scripts import *

from pareto.components.preprocessor import preprocess

from pareto.components.env import synth_env

"""
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cloudformation-limits.html
"""

Metrics={
    "resources": (lambda x: (len(x["Resources"]) if "Resources" in x else 0)/200),
    "outputs": (lambda x: (len(x["Outputs"]) if "Outputs" in x else 0)/60),
    "template_size": (lambda x: (len(json.dumps(x))/51200))
    }

def init_region(config):
    region=boto3.session.Session().region_name
    if region in ['', None]:
        raise RuntimeError("region is not set in AWS profile")
    config["globals"]["region"]=region

class S3Keys(list):

    def __init__(self, config):
        list.__init__(self)
        paginator=S3.get_paginator("list_objects_v2")
        pages=paginator.paginate(Bucket=config["globals"]["bucket"],
                                 Prefix="%s/lambdas" % config["globals"]["app"])
        for struct in pages:
            if "Contents" in struct:
                self+=[obj["Key"] for obj in struct["Contents"]]
                
    @property
    def latest(self):
        keys={}
        for s3key in sorted(self):
            key=LambdaKey.parse(s3key)
            keys[key["name"]]=s3key
        return keys

    @property
    def commits(self):
        keys={}
        for s3key in self:
            key=LambdaKey.parse(s3key)
            keys.setdefault(key["name"], {})
            keys[key["name"]][key["hexsha"]]=s3key
        return keys

    def assign(self, components):
        latest, commits = self.latest, self.commits
        keys, errors = {}, []
        for component in filter_functions(components):
            if "commit" in component:
                if component["commit"] in commits[component["name"]]:
                    keys[component["name"]]=commits[component["name"]][component["commit"]]
                else:
                    errors.append("commit %s not found for %s" % (component["commit"], component["name"]))
            else:
                if component["name"] in latest:
                    keys[component["name"]]=latest[component["name"]]
                else:
                    errors.append("no deployables found for %s" % component["name"])
        return keys, errors
    
def add_staging(config):
    logging.info("adding staging")
    def add_staging(components, keys):
        for component in filter_functions(components):
            component["staging"]={"bucket": config["globals"]["bucket"],
                                  "key": keys[component["name"]]}
    def dump_keys(keys):
        for k, v in keys.items():
            logging.info("%s => %s" % (k, v))
    s3keys=S3Keys(config)
    keys, errors = s3keys.assign(config["components"])
    if errors!=[]:
        raise RuntimeError(", ".join(errors))
    add_staging(config["components"], keys)
    dump_keys(keys)                    

"""
- cloudformation will check this for you early in deployment process
- but still better to have local version to get early warning I think
- in particular is effective at checking references to logical id which may have been incorrectly coded within components
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
    filename="tmp/env-%s.yaml" % timestamp()
    yaml.SafeDumper.ignore_aliases=lambda *args: True
    with open(filename, 'w') as f:
        f.write(yaml.safe_dump(env,
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
        """, Loader=yaml.FullLoader)
        args=argsparse(sys.argv[1:], argsconfig)
        config=args.pop("config")
        config["globals"]["stage"]=args.pop("stage")
        init_region(config)    
        validate_bucket(config)
        preprocess(config)
        add_staging(config)
        env=synth_env(config)
        check_refs(env)
        check_metrics(env)
        dump_env(env)
        push_templates(config, env)
        # deploy_env(config, env["master"])
    except ClientError as error:
        logging.error(error)                      
    except WaiterError as error:
        logging.error(error)                      
    except RuntimeError as error:
        logging.error(error)                      


        
