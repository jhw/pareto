from pareto.components import *

DDBTypes=yaml.safe_load("""
string: S
int: N
float: N
""")

@resource()
def Table(stream={"type": "NEW_IMAGE"},
          **kwargs):        
    primaryfield=[field
                  for field in kwargs["fields"]
                  if ("primary" in field
                      and field["primary"])].pop()
    keyschema=[{"AttributeName": primaryfield["name"],
                "KeyType": "HASH"}]
    attributes=[{"AttributeName": field["name"],
                 "AttributeType": DDBTypes[field["type"]]}
                for field in kwargs["fields"]
                if (("primary" in field and
                     field["primary"]) or
                    ("index" in field and
                     field["index"]))]
    indexes=[{"IndexName": "%s-index" % field["name"],
              "Projection": {"ProjectionType": "ALL"},
              "KeySchema": [{"AttributeName": field["name"],
                             "KeyType": "HASH"}]}
             for field in kwargs["fields"]
             if ("index" in field and
                 field["index"] and
                 field["type"]=="string")]
    props={"BillingMode": "PAY_PER_REQUEST", 
           "AttributeDefinitions": attributes,
           "KeySchema": keyschema,
           "TableName": resource_name(kwargs)}
    if indexes!=[]:
        props["GlobalSecondaryIndexes"]=indexes
    if "action" in kwargs:
        props["StreamSpecification"]={"StreamViewType": stream["type"]}
    return "AWS::DynamoDB::Table", props

@resource(suffix="mapping")
def TableMapping(**kwargs):
    target=ref("%s-arn" % kwargs["action"])
    source=fn_getatt(kwargs["name"], "StreamArn")
    props={"FunctionName": target,
           "EventSourceArn": source,
           "StartingPosition": "LATEST"}
    return "AWS::Lambda::EventSourceMapping", props

def synth_table(template, **kwargs):
    template.update(Resources=Table(**kwargs))
    if "action" in kwargs:
        template.update(Parameters=parameter("%s-arn" % kwargs["action"]),
                        Resources=TableMapping(**kwargs))

if __name__=="__main__":
    pass
