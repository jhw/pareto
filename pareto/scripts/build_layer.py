#!/usr/bin/env python

"""
- codebuild unfortunately doesn't seem to have any waiters (despite apparent boto3 support) so you have to roll your own
- https://stackoverflow.com/questions/53733423/how-to-wait-for-a-codebuild-project-to-finish-building-before-finishing-a-boto3
"""

from pareto.scripts import *

from jinja2 import Template

import time

CB=boto3.client("codebuild")

LatestBuildSpec="""
version: {{ version }}
phases:
  install:
    runtime-versions:
      python: {{ runtime }}
    commands:
      - mkdir -p build/python
      - pip install --upgrade pip
      - pip install --upgrade --target build/python {{ package.name }}
artifacts:
  files:
    - '**/*'
  base-directory: build
  name: {{ package.name }}-LATEST.zip
"""

VersionedBuildSpec="""
version: {{ version }}
phases:
  install:
    runtime-versions:
      python: {{ runtime }}
    commands:
      - mkdir -p build/python
      - pip install --upgrade pip
      - pip install --upgrade --target build/python {{ package.name }}=={{ package.version.raw }}
artifacts:
  files:
    - '**/*'
  base-directory: build
  name: {{ package.name }}-{{ package.version.formatted }}.zip
"""

def project_name(config, package):
    return "%s-%s-layer" % (config["globals"]["app"],
                            package["name"])

def validate_package(fn):
    def wrapped(packagestr):
        if ("-" in packagestr and
            not re.search("\\-(\\d+\\.)*\\d+$", packagestr)):
            raise RuntimeError("package definition has invalid format")
        return fn(packagestr)
    return wrapped

@validate_package
def parse_package(packagestr):
    tokens=packagestr.split("-")
    package={"name": tokens[0]}
    if len(tokens) > 1:
        package["version"]={"raw": tokens[1],
                            "formatted": tokens[1].replace(".", "-")}
    return package

def reset_project(fn,
                  maxtries=10,
                  wait=1):
    def wrapped(config, package):
        projectname=project_name(config, package)
        for i in range(maxtries):
            projects=CB.list_projects()["projects"]
            if projectname in projects:
                logging.warning("project exists; deleting ..")
                CB.delete_project(name=projectname)
                time.sleep(wait)
            else:
                return fn(config, package)
        projects=CB.list_projects()["projects"]
        if projectname in projects:
            raise RuntimeError("%s already exists" % projectname)
    return wrapped

@reset_project
def init_project(config, package):
    logging.info("creating project")
    def format_args(args):
        return [{"name": name,
                 "value": value}
                for name, value in args.items()]
    env={"type": "LINUX_CONTAINER",
         "image": "aws/codebuild/standard:2.0",
         "computeType": "BUILD_GENERAL1_SMALL"}
    args={"version": "0.2",
          "package": package,
          "runtime": config["globals"]["runtime"]}
    buildspec=VersionedBuildSpec if "version" in package else LatestBuildSpec
    template=Template(buildspec).render(args)
    print (template)
    print ()
    source={"type": "NO_SOURCE",
            "buildspec": template}
    artifacts={"type": "S3",
               "location": config["globals"]["bucket"],
               "path": "%s/layers" % config["globals"]["app"],
               "overrideArtifactName": True, # default is CB project name
               "packaging": "ZIP"}
    return CB.create_project(name=project_name(config, package),
                             source=source,
                             artifacts=artifacts,
                             environment=env,
                             serviceRole=config["globals"]["role"])

def run_project(config, package,
                wait=3,
                maxtries=100,
                exitcodes=["SUCCEEDED",
                           "FAILED",
                           "STOPPED"]):
    logging.info("running project")
    def get_build(projectname):
        resp=CB.list_builds_for_project(projectName=projectname)
        if ("ids" not in resp or
            resp["ids"]==[]):
            raise RuntimeError("no build ids found")
        return CB.batch_get_builds(ids=resp["ids"])["builds"].pop()
    projectname=project_name(config, package)    
    CB.start_build(projectName=projectname)
    for i in range(maxtries):
        time.sleep(wait)
        build=get_build(projectname)
        logging.info("%i/%i\t%s\t%s" % (1+i,
                                        maxtries,
                                        build["currentPhase"],
                                        build["buildStatus"]))
        if build["buildStatus"] in exitcodes:
            break
    
if __name__=="__main__":
    try:
        init_stdout_logger(logging.INFO)
        argsconfig=yaml.load("""
        - name: config
          type: file
        - name: package
          type: str
        """, Loader=yaml.FullLoader)
        args=argsparse(sys.argv[1:], argsconfig)
        config=args.pop("config")
        validate_bucket(config)
        package=parse_package(args.pop("package"))
        init_project(config, package)
        run_project(config, package)
    except ClientError as error:
        logging.error(str(error))
    except RuntimeError as error:
        logging.error(str(error))

