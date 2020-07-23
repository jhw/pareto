from pareto.components import *

TriggerConfig=yaml.load("""
bucket:
  iam_name: s3
  event_sourced: false
website:
  iam_name: s3
  event_sourced: false
table:
  iam_name: dynamodb
  event_sourced: true
queue:
  iam_name: sqs
  event_sourced: true
""", Loader=yaml.FullLoader)

def add_types(functypes=["apis", "actions"], **components):
    for attr in components:
        for component in components[attr]:
            component["type"]=attr[:-1]
            component["functional"]=attr in functypes

def validate(**components):
    def assert_unique(**components):
        keys=[]
        for attr in components:
            keys+=[component["name"]
                   for component in components[attr]]
        ukeys=list(set(keys))
        if len(keys)!=len(ukeys):
            raise RuntimeError("keys are not unique")
    for fn in [assert_unique]:
        fn(**components)
            
def preprocess(config):
    for fn in [validate]:
        fn(**config["components"])
        
if __name__=="__main__":
    try:
        import os, sys
        if len(sys.argv) < 2:
            raise RuntimeError("Please enter filename")
        filename=sys.argv[1]
        if not os.path.exists(filename):
            raise RuntimeError("File does not exist")
        if not filename.endswith(".yaml"):
            raise RuntimeError("File must be a yaml file")
        with open(filename, 'r') as f:
            config=yaml.load(f.read(),
                             Loader=yaml.FullLoader)
        preprocess(config)
        yaml.SafeDumper.ignore_aliases=lambda *args: True
        print (yaml.safe_dump(config,
                              default_flow_style=False))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
