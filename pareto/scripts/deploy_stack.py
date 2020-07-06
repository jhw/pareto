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

def load_config(configfile, stagename):
    with open(configfile, 'r') as f:
        config=yaml.load(f.read(),
                         Loader=yaml.FullLoader)
    config["app"]=Config["AppName"]
    config["region"]=Config["AWSRegion"]
    config["bucket"]=Config["S3StagingBucket"]
    config["stage"]=stagename
    return config

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
        return "%s/%s-%s.zip" % (config["app"],
                                 name,
                                 timestamp)
    ts=timestamp()
    for component in filter_functions(config["components"]):
        key=lambda_key(component["name"], ts)
        component["staging"]={"bucket": config["bucket"],
                              "key": key}

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
        # logging.info("pushing %s lambda" % component["name"])
        validate_lambda(component)
        zfname=init_zipfile(component)
        push_lambda(component, zfname)

def calc_metrics(templates, metrics=Metrics):
    logging.info("calculating template metrics")
    def calc_metrics(tempname, template, metrics):
        outputs={"name": tempname}
        outputs.update({metrickey: metricfn(template)
                        for metrickey, metricfn in metrics.items()})
        return outputs
    def validate_metrics(metrics):
        for row in metrics:
            for attr in row.keys():
                if attr=="name":
                    continue
                if row[attr]:
                    raise RuntimeError("%s %s > 100%" % (row["name"],
                                                         row[attr]))
    metrics=[calc_metrics(tempname, template, metrics)
             for tempname, template in templates.items()]
    print ("\n%s\n" % pd.DataFrame(metrics))

def push_templates(config, templates):
    logging.info("pushing templates")
    def push_template(config, tempname, template):
        key="%s-%s/templates/%s.json" % (config["app"],
                                         config["stage"],
                                         tempname)
        logging.info("pushing %s" % key)
        body=json.dumps(template).encode("utf-8")
        S3.put_object(Bucket=config["bucket"],
                      Key=key,
                      Body=body,
                      ContentType='application/json')
    for tempname, template in templates.items():
        if tempname=="master":
            continue
        push_template(config, tempname, template)
    
if __name__=="__main__":
    try:
        init_stdout_logger(logging.INFO)
        if len(sys.argv) < 3:
            raise RuntimeError("please enter config file, stage name")
        configfile, stagename = sys.argv[1:3]
        if not configfile.endswith(".yaml"):
            raise RuntimeError("config must be a yaml file")
        if not os.path.exists(configfile):
            raise RuntimeError("config file does not exist")
        if stagename not in ["dev", "prod"]:
            raise RuntimeError("stage name is invalid")
        config=load_config(configfile, stagename)
        preprocess(config)
        run_tests(config)
        add_staging(config)
        push_lambdas(config)
        env=synth_env(config)
        calc_metrics(env)
        push_templates(config, env)
        print (yaml.safe_dump(env["master"],
                              default_flow_style=False))
    except ClientError as error:
        logging.error(error)                      
    except WaiterError as error:
        logging.error(error)                      
    except RuntimeError as error:
        logging.error(error)                      


        
