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

def project_name(config):
    return "%s-%s-layer" % (config["globals"]["app"],
                            config["build"]["package"])

"""
- aws codebuild delete-project --name pareto-demo-pyyaml-layer aws codebuild delete-project --name pareto-demo-pyyaml-layer
"""

def init_project(config, buildspec):
    def format_args(args):
        return [{"name": name,
                 "value": value}
                for name, value in args.items()]
    env={"type": "LINUX_CONTAINER",
         "image": "aws/codebuild/standard:2.0",
         "computeType": "BUILD_GENERAL1_SMALL",
         "environmentVariables": []}
    args={"version": "0.2",
          "package": config["build"]["package"],
          "runtime": config["build"]["runtime"]}
    template=Template(buildspec).render(args)
    print (template)
    source={"type": "NO_SOURCE",
            "buildspec": template}
    artifacts={"type": "S3",
               "location": config["globals"]["bucket"],
               "path": "%s/layers" % config["globals"]["app"],
               "overrideArtifactName": True,
               "packaging": "ZIP"}
    return CB.create_project(name=project_name(config),
                             source=source,
                             artifacts=artifacts,
                             environment=env,
                             serviceRole=config["build"]["role"])

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
        # START TEMP CODE
        config["build"]={"package": args["package"],
                         "runtime": "3.7",
                         "role": "arn:aws:iam::119552584133:role/slow-russian-codebuild"}
        # END TEMP CODE
        init_project(config, LatestBuildSpec)
        print (CB.start_build(projectName=project_name(config))["build"]["arn"])
    except ClientError as error:
        logging.error(str(error))
    except RuntimeError as error:
        logging.error(str(error))

