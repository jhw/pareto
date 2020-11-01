#!/usr/bin/env python

"""
- codebuild unfortunately doesn't seem to have any waiters (despite apparent boto3 support) so you have to roll your own
- https://stackoverflow.com/questions/53733423/how-to-wait-for-a-codebuild-project-to-finish-building-before-finishing-a-boto3
"""

from pareto.scripts import *

RolePolicyDoc=yaml.safe_load("""
Statement:
  - Action: sts:AssumeRole
    Effect: Allow
    Principal:
      Service: codebuild.amazonaws.com
Version: '2012-10-17'
""")

"""
- https://docs.aws.amazon.com/codebuild/latest/userguide/build-env-ref-available.html
- image affects python versions available
"""

DockerImage="aws/codebuild/standard:4.0"

def layer_project_name(config, pkg):
    return "%s-%s-layer" % (config["globals"]["app"],
                            pkg["name"])

"""
- https://stackoverflow.com/questions/46584324/code-build-continues-after-build-fails
"""

def init_build_spec(config, layer,
                    version="0.2"):
    def init_install_phase(config, layer):
        rtversions={"python": config["globals"]["runtime"]}
        commands=["mkdir -p build/python",
                  "pip install --upgrade pip"]
        for package in layer["packages"]:
            if "repo" in package:
                host=package["repo"]["host"]
                if not host.endswith(".com"):
                    host+=".com"
                source="git+https://%s/%s/%s" % (host,
                                                 package["repo"]["owner"],
                                                 package["name"])
                if "version" in package:
                    source+="@%s" % package["version"]
            else:
                source=package["name"]
                if "version" in package:
                    source+="==%s" % package["version"]
            commands.append("pip install --upgrade --target build/python %s" % source)
        return {"runtime-versions": rtversions,
                "commands": commands}
    def format_requirements(layer):
        def format_package(package):
            if "version" in package:
                return "%s==%s" % (package["name"],
                                   package["version"])
            else:
                return package["name"]
        return "\n".join([format_package(package)
                          for package in layer["packages"]])
    def init_postbuild_phase(config, layer):
        commands=["echo \"%s\" > build/requirements.txt" % format_requirements(layer),
                  'bash -c "if [ /"$CODEBUILD_BUILD_SUCCEEDING/" == /"0/" ]; then exit 1; fi"']
        return {"commands": commands}
    def init_phases(config, layer):
        return {"install": init_install_phase(config, layer),
                "post_build": init_postbuild_phase(config, layer)}
    def init_artifacts(config, layer):
        return {"files": ["**/*"],
                "base-directory": "build",
                "name": "%s.zip" % layer["name"]}
    return {"version": version,
            "phases": init_phases(config, layer),
            "artifacts": init_artifacts(config, layer)}

"""
- need to reset project / create new one because `buildspec` (the thing that likely gets changed) is part of the `source` arg passed to `create_project` :/
"""

def reset_project(fn,
                  maxtries=10,
                  wait=1):
    def wrapped(cb, iam, config, layer):
        projectname=layer_project_name(config, layer)
        for i in range(maxtries):
            projects=cb.list_projects()["projects"]
            if projectname in projects:
                logging.warning("project exists; deleting ..")
                cb.delete_project(name=projectname)
                time.sleep(wait)
            else:
                return fn(cb, iam, config, layer)
        projects=cb.list_projects()["projects"]
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
    def create_role(iam,
                    rolename,
                    permissions=["codebuild:*",
                                 "s3:*",
                                 "logs:*"],
                    rolepolicydoc=RolePolicyDoc):
        role=iam.create_role(RoleName=rolename,
                             AssumeRolePolicyDocument=json.dumps(rolepolicydoc))
        policydoc={"Statement": [{"Action": permission,
                                  "Effect": "Allow",
                                  "Resource": "*"}
                                 for permission in permissions],
                   "Version": "2012-10-17"}
        policy=iam.create_policy(PolicyName=policy_name(rolename),
                                 PolicyDocument=json.dumps(policydoc))
        logging.info("waiting for policy creation ..")
        waiter=iam.get_waiter("policy_exists")
        waiter.wait(PolicyArn=policy["Policy"]["Arn"])
        iam.attach_role_policy(RoleName=rolename,
                               PolicyArn=policy["Policy"]["Arn"])
        return role["Role"]["Arn"]
    def wrapped(cb, iam, config, layer):
        rolename=admin_role_name(config)
        rolearns={role["RoleName"]:role["Arn"]
                  for role in iam.list_roles()["Roles"]}
        if rolename in rolearns:
            logging.info("admin role exists")
            rolearn=rolearns[rolename]
        else:
            logging.warning("creating admin role")
            rolearn=create_role(iam, rolename)
            logging.info("waiting for role creation ..")
            waiter=iam.get_waiter("role_exists")
            waiter.wait(RoleName=rolename)
        return fn(cb, iam, config, layer, rolearn)
    return wrapped

@reset_project
@assert_role
def init_project(cb, iam, config, layer, rolearn,
                 env={"type": "LINUX_CONTAINER",
                      "image": DockerImage,
                      "computeType": "BUILD_GENERAL1_SMALL"},
                 maxtries=20,
                 wait=3):
    logging.info("creating project")
    buildspec=init_build_spec(config, layer)
    template=yaml.safe_dump(buildspec,
                            default_flow_style=False)
    print (template)
    print ()
    source={"type": "NO_SOURCE",
            "buildspec": template}
    artifacts={"type": "S3",
               "location": config["globals"]["bucket"],
               "path": "%s/layers" % config["globals"]["app"],
               "overrideArtifactName": True,
               "packaging": "ZIP"}
    """
    - because sometimes the iam role hasn't been propagated properly
    - and the waiters don't catch it
    - ERROR - An error occurred (InvalidInputException) when calling the CreateProject operation: CodeBuild is not authorized to perform: sts:AssumeRole on arn:aws:iam::119552584133:role/pareto-demo-admin-role
    """
    projectname=layer_project_name(config, layer)
    for i in range(maxtries):
        try:
            logging.info("trying to create project [%i/%i]" % (i+1, maxtries))
            project=cb.create_project(name=projectname,
                                      source=source,
                                      artifacts=artifacts,
                                      environment=env,
                                      serviceRole=rolearn)
            logging.info("project created :)")
            return project
        except ClientError as error:
            time.sleep(wait)
    raise RuntimeError("couldn't create codebuild project")
                          
def run_project(cb, config, layer,
                wait=3,
                maxtries=100,
                exitcodes=["SUCCEEDED",
                           "FAILED",
                           "STOPPED"]):
    logging.info("running project")
    def get_build(cb, projectname):
        resp=cb.list_builds_for_project(projectName=projectname)
        if ("ids" not in resp or
            resp["ids"]==[]):
            raise RuntimeError("no build ids found")
        return cb.batch_get_builds(ids=resp["ids"])["builds"].pop()
    projectname=layer_project_name(config, layer)    
    cb.start_build(projectName=projectname)
    for i in range(maxtries):
        time.sleep(wait)
        build=get_build(cb, projectname)
        logging.info("%i/%i\t%s\t%s" % (1+i,
                                        maxtries,
                                        build["currentPhase"],
                                        build["buildStatus"]))
        if build["buildStatus"] in exitcodes:
            break
    
if __name__=="__main__":
    try:
        init_stdout_logger(logging.INFO)
        argsconfig=yaml.safe_load("""
        - name: config
          type: file
        - name: layer
          type: str
        """)
        args=argsparse(sys.argv[1:], argsconfig)
        config=args.pop("config")
        validate_bucket(config, boto3.client("s3"))
        if "layers" not in config["components"]:
            raise RuntimeError("no layers found")
        layers={layer["name"]:layer
                for layer in config["components"]["layers"]}
        if args["layer"] not in layers:
            raise RuntimeError("layer not found")
        layer=layers[args["layer"]]
        cb=boto3.client("codebuild")
        iam=boto3.client("iam")
        init_project(cb, iam, config, layer)
        run_project(cb, config, layer)
    except ClientError as error:
        logging.error(str(error))
    except RuntimeError as error:
        logging.error(str(error))

