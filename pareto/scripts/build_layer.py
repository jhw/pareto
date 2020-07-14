#!/usr/bin/env python

"""
- codebuild unfortunately doesn't seem to have any waiters (despite apparent boto3 support) so you have to roll your own
- https://stackoverflow.com/questions/53733423/how-to-wait-for-a-codebuild-project-to-finish-building-before-finishing-a-boto3
"""

"""
- requires arn:aws:iam::aws:policy/AdministratorAccess
"""

from pareto.scripts import *

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

def reset_project(fn,
                  maxtries=10,
                  wait=1):
    def wrapped(config, package):
        projectname=layer_project_name(config, package)
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

def assert_role(fn):
    def wrapped(config, package):
        return fn(config, package,
                  "arn:aws:iam::119552584133:role/slow-russian-codebuild")
    return wrapped

@reset_project
@assert_role
def init_project(config, package, rolearn):
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
               "overrideArtifactName": True,
               "packaging": "ZIP"}
    return CB.create_project(name=layer_project_name(config, package),
                             source=source,
                             artifacts=artifacts,
                             environment=env,
                             serviceRole=rolearn)

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
    projectname=layer_project_name(config, package)    
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
        package=parse_layer_package(args.pop("package"))
        init_project(config, package)
        run_project(config, package)
    except ClientError as error:
        logging.error(str(error))
    except RuntimeError as error:
        logging.error(str(error))
