#!/usr/bin/env python

from pareto.scripts import *

CB=boto3.client("codebuild")

BuildSpec="""
version: 0.2
phases:
  install:
    runtime-versions:
      python: $RUNTIME_VERSION
    commands:
      - echo "running install phase"
      - apt-get update
      - apt-get install zip python3-pip -y
      - mkdir -p build/python
      - pip3 install --upgrade --target build/python pyyaml
artifacts:
  files:
    - '**/*'
  base-directory: build
  name: yaml-LATEST.zip
"""

def project_name(config):
    return "%s-lxml-layer" % config["globals"]["app"]    

def init_project(config, buildspec):
    def format_args(args):
        return [{"name": name,
                 "value": value}
                for name, value in args.items()]
    args={"RUNTIME_VERSION": config["globals"]["runtime"]}
    env={"type": "LINUX_CONTAINER",
         "image": "aws/codebuild/standard:2.0",
         "computeType": "BUILD_GENERAL1_SMALL",
         "environmentVariables": format_args(args)}
    source={"type": "NO_SOURCE",
            "buildspec": buildspec}
    artifacts={"type": "S3",
               "location": config["globals"]["bucket"],
               "path": "%s/layers" % config["globals"]["app"],
               "overrideArtifactName": True,
               "packaging": "ZIP"}
    return CB.create_project(name=project_name(config),
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
        """, Loader=yaml.FullLoader)
        args=argsparse(sys.argv[1:], argsconfig)
        config=args.pop("config")
        validate_bucket(config)
        # START TEMP CODE
        config["globals"]["role"]="arn:aws:iam::119552584133:role/slow-russian-codebuild"
        config["globals"]["runtime"]="3.7"
        # END TEMP CODE
        init_project(config, BuildSpec)
        print (CB.start_build(projectName=project_name(config))["build"]["arn"])
    except ClientError as error:
        logging.error(str(error))
    except RuntimeError as error:
        logging.error(str(error))

