import logging, os, re

"""
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cloudformation-limits.html
"""

def list_profiles():
    config=open("%s/.aws/config" % os.path.expanduser("~")).read()
    return [re.sub("profile ", "", row[1:-1])
            for row in config.split("\n")
            if (len(row) > 2 and
                row[0]=="[" and
                row[-1]=="]")]

"""
- temporarily disable AWS creds whilst running tests to avoid messing with production environment :-/
- must have an AWS profile entitled `dummy` for this to work
"""

def toggle_aws_profile(fn, profiles=list_profiles()):
    def wrapped(config={}, dummy="dummy"):
        profile=os.environ["AWS_PROFILE"]
        if dummy not in profiles:
            raise Runtime("`%s` profile not found" % dummy)
        logging.info("blanking AWS profile")
        os.environ["AWS_PROFILE"]=dummy
        resp=fn(config)
        logging.info("resetting AWS profile")
        os.environ["AWS_PROFILE"]=profile
        return resp
    return wrapped
