#!/usr/bin/env python

from pareto.scripts import *

import unittest, zipfile

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

@toggle_aws_profile
def run_tests(config):
    logging.info("running tests")
    def index_test(component, klassname="IndexTest"):    
        modname="%s.test" % underscore(component["name"])
        try:
            mod=__import__(modname, fromlist=[klassname])
        except ModuleNotFoundError:
            raise RuntimeError("%s does not exist" % modname)
        klass=getattr(mod, klassname)
        if not klass:
            raise RuntimeError("%s does not exist in %s" % (klassname,
                                                            modname))
        return klass
    klasses=[index_test(component)
             for component in filter_functions(config["components"])]
    suite=unittest.TestSuite()
    for klass in klasses:
        suite.addTest(unittest.makeSuite(klass))
    runner=unittest.TextTestRunner()
    results=runner.run(suite)
    nfailures, nerrors = len(results.failures), len(results.errors)
    if (nfailures > 0 or nerrors > 0):
        raise RuntimeError("Tests failed with %i failures / %i errors" % (nfailures, nerrors))        
    return results

def add_staging(config):
    logging.info("adding staging")
    def lambda_key(name, timestamp):
        return "%s/lambdas/%s-%s.zip" % (config["globals"]["app"],
                                         name,
                                         timestamp)
    ts=timestamp()
    for component in filter_functions(config["components"]):
        key=lambda_key(component["name"], ts)
        component["staging"]={"bucket": config["globals"]["bucket"],
                              "key": key}

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

def push_lambdas(config):
    logging.info("pushing lambdas")
    def validate_lambda(component):
        if not os.path.exists("lambda/%s" % underscore(component["name"])):
            raise RuntimeError("%s lambda does not exist" % component["name"])
    def is_valid(filename, ignore=["test.py$",
                                   ".pyc$"]):
        for pat in ignore:
            if re.search(pat, filename)!=None:
                return False
        return True
    def write_zipfile(component, zf):
        path, count = "lambda/%s" % underscore(component["name"]), 0
        for root, dirs, files in os.walk(path):
            for filename in files:
                if is_valid(filename):
                    zf.write(os.path.join(root, filename),
                             arcname=filename)
                    count+=1
        if not count:
            raise RuntimeError("no files found in %s" % path)
    def init_zipfile(component):
        zfname="tmp/%s" % component["staging"]["key"].split("/")[-1]
        zf=zipfile.ZipFile(zfname, 'w', zipfile.ZIP_DEFLATED)
        write_zipfile(component, zf)
        zf.close()
        return zfname
    def push_lambda(component, zfname):
        logging.info("pushing %s" % component["staging"]["key"])
        S3.upload_file(zfname,
                       component["staging"]["bucket"],
                       component["staging"]["key"],
                       ExtraArgs={'ContentType': 'application/zip'})
    for component in filter_functions(config["components"]):
        validate_lambda(component)
        zfname=init_zipfile(component)
        push_lambda(component, zfname)
        
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
        config=load_config(sys.argv)
        preprocess(config)
        run_tests(config)
        add_staging(config)
        env=synth_env(config)
        check_refs(env)
        check_metrics(env)
        dump_env(env)
        push_templates(config, env)
        push_lambdas(config)
        deploy_env(config, env["master"])
    except ClientError as error:
        logging.error(error)                      
    except WaiterError as error:
        logging.error(error)                      
    except RuntimeError as error:
        logging.error(error)                      


        
