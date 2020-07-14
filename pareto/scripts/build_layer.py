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
      - pip install --upgrade --target build/python {{ package }}
artifacts:
  files:
    - '**/*'
  base-directory: build
  name: {{ package }}-LATEST.zip
"""

def project_name(config, package):
    return "%s-%s-layer" % (config["globals"]["app"],
                            package)

"""
aws codebuild delete-project --name pareto-demo-pymorphy2-layer

"""

def init_project(config, package,
                 buildspec=LatestBuildSpec):
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
    template=Template(buildspec).render(args)
    source={"type": "NO_SOURCE",
            "buildspec": template}
    artifacts={"type": "S3",
               "location": config["globals"]["bucket"],
               "path": "%s/layers" % config["globals"]["app"],
               "overrideArtifactName": True,
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
        init_project(config, args["package"])
        print (CB.start_build(projectName=project_name(config, args["package"]))["build"]["arn"])
    except ClientError as error:
        logging.error(str(error))
    except RuntimeError as error:
        logging.error(str(error))

