from pareto.components import *

DDBTypes=yaml.load("""
string: S
int: N
float: N
""", Loader=yaml.FullLoader)

EventMappingPermissions=yaml.load("""
- dynamodb:GetRecords
- dynamodb:GetShardIterator
- dynamodb:DescribeStream
- dynamodb:ListStreams 
""", Loader=yaml.FullLoader)

@resource()
def Table(stream={"type": "NEW_IMAGE"},
          **kwargs):        
    """
    - primary key currently defined as single field hash
    - ie no range key currently
    """
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
    """
    - can have a hash- style GSI on any STRING field you want
    - *think* you want ProjectionType=ALL but not 100% sure
      - https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-dynamodb-gsi.html
    - ProvisionedThroughput not required for index and hopefully covered by BillingType=PAY_PER_REQUEST
    """
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

@event_mapping_permissions(EventMappingPermissions)
def synth_table(**kwargs):
    template=Template(resources=[Table(**kwargs)])
    if "action" in kwargs:
        template.parameters.append(parameter("%s-arn" % kwargs["action"]))
        template.resources.append(TableMapping(**kwargs))
    return template

if __name__=="__main__":
    pass
