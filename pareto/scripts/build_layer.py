#!/usr/bin/env python

from pareto.scripts import *

from jinja2 import Template

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

"""
aws codebuild delete-project --name pareto-demo-pymorphy2-layer
"""

def init_project(config, package):
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
    print ("\n%s\n" % template)
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
        print (CB.start_build(projectName=project_name(config, package)))
    except ClientError as error:
        logging.error(str(error))
    except RuntimeError as error:
        logging.error(str(error))

