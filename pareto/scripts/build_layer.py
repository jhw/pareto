#!/usr/bin/env python

"""
- codebuild unfortunately doesn't seem to have any waiters (despite apparent boto3 support) so you have to roll your own
- https://stackoverflow.com/questions/53733423/how-to-wait-for-a-codebuild-project-to-finish-building-before-finishing-a-boto3
"""

from pareto.scripts import *

from pareto.staging.layers import *

RolePolicyDoc=yaml.load("""
Statement:
  - Action: sts:AssumeRole
    Effect: Allow
    Principal:
      Service: codebuild.amazonaws.com
Version: '2012-10-17'
""", Loader=yaml.FullLoader)

"""
- https://stackoverflow.com/questions/46584324/code-build-continues-after-build-fails
"""

BuildSpec="""
version: {{ version }}
phases:
  install:
    runtime-versions:
      python: {{ runtime }}
    commands:
      - mkdir -p build/python
      - pip install --upgrade pip
      - pip install --upgrade --target build/python {{ package.pip_source }}
  post_build:
    commands:
      - bash -c "if [ /"$CODEBUILD_BUILD_SUCCEEDING/" == /"0/" ]; then exit 1; fi"
artifacts:
  files:
    - '**/*'
  base-directory: build
  name: {{ package.artifacts_name }}
"""

"""
- need to reset project / create new one because `buildspec` (the thing that likely gets changed) is part of the `source` arg passed to `create_project` :/
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

"""
- https://www.reddit.com/r/aws/comments/dzsi8x/exact_same_assumerole_document_still_getting/
"""

def assert_role(fn):
    def admin_role_name(config):
        return "%s-admin-role" % config["globals"]["app"]
    def policy_name(rolename):
        return "%s-policy" % rolename
    def create_role(rolename,
                    permissions=["codebuild:*",
                                 "s3:*",
                                 "logs:*"],
                    rolepolicydoc=RolePolicyDoc):
        role=IAM.create_role(RoleName=rolename,
                             AssumeRolePolicyDocument=json.dumps(rolepolicydoc))
        policydoc={"Statement": [{"Action": permission,
                                  "Effect": "Allow",
                                  "Resource": "*"}
                                 for permission in permissions],
                   "Version": "2012-10-17"}
        policy=IAM.create_policy(PolicyName=policy_name(rolename),
                                 PolicyDocument=json.dumps(policydoc))
        logging.info("waiting for policy creation ..")
        waiter=IAM.get_waiter("policy_exists")
        waiter.wait(PolicyArn=policy["Policy"]["Arn"])
        IAM.attach_role_policy(RoleName=rolename,
                               PolicyArn=policy["Policy"]["Arn"])
        return role["Role"]["Arn"]
    def wrapped(config, package):
        rolename=admin_role_name(config)
        rolearns={role["RoleName"]:role["Arn"]
                  for role in IAM.list_roles()["Roles"]}
        if rolename in rolearns:
            logging.info("admin role exists")
            rolearn=rolearns[rolename]
        else:
            logging.warning("creating admin role")
            rolearn=create_role(rolename)
            logging.info("waiting for role creation ..")
            waiter=IAM.get_waiter("role_exists")
            waiter.wait(RoleName=rolename)
        return fn(config, package, rolearn)
    return wrapped

@reset_project
@assert_role
def init_project(config, package, rolearn,
                 buildspec=BuildSpec,
                 maxtries=20,
                 wait=3):
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
    projectname=layer_project_name(config, package)
    template=Template(buildspec).render(args)
    print (template)
    print ()
    source={"type": "NO_SOURCE",
            "buildspec": template}
    artifacts={"type": "S3",
               "location": config["globals"]["bucket"],
               "path": "%s/layers/%s" % (config["globals"]["app"],
                                         package["name"]),
               "overrideArtifactName": True,
               "packaging": "ZIP"}
    """
    - because sometimes the iam role hasn't been propagated properly
    - and the waiters don't catch it
    - ERROR - An error occurred (InvalidInputException) when calling the CreateProject operation: CodeBuild is not authorized to perform: sts:AssumeRole on arn:aws:iam::119552584133:role/pareto-demo-admin-role
    """
    for i in range(maxtries):
        try:
            logging.info("trying to create project [%i/%i]" % (i+1, maxtries))
            project=CB.create_project(name=projectname,
                                      source=source,
                                      artifacts=artifacts,
                                      environment=env,
                                      serviceRole=rolearn)
            logging.info("project created :)")
            return project
        except ClientError as error:
            time.sleep(wait)
    raise RuntimeError("couldn't create codebuild project")
                            
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
        package=LayerPackage.create_cli(config,
                                        args.pop("package"))
        init_project(config, package)
        run_project(config, package)
    except ClientError as error:
        logging.error(str(error))
    except RuntimeError as error:
        logging.error(str(error))

