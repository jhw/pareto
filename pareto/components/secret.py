from pareto.components import *

@resource(suffix="secret")
def Secret(**kwargs):
    secret=kwargs["value"] if type(kwargs["value"])==str else json.dumps(kwargs["value"])
    props={"Name": kwargs["name"],
           "SecretString": secret}
    return "AWS::SecretsManager::Secret", props

def synth_secret(**kwargs):
    return Template(Resources=[Secret(**kwargs)])

if __name__=="__main__":
    pass
