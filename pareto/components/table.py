from pareto.components import *

def synth_table(**kwargs):
    DDBTypes={"string": "S",
              "int": "N",
              "float": "N"}
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
               "TableName": resource_id(kwargs)}
        if indexes!=[]:
            props["GlobalSecondaryIndexes"]=indexes
        if "action" in kwargs:
            props["StreamSpecification"]={"StreamViewType": stream["type"]}
        return "AWS::DynamoDB::Table", props
    def LambdaMapping(**kwargs):
        suffix="%s-mapping" % kwargs["action"]["name"]
        @resource(suffix)
        def LambdaMapping(**kwargs):
            funcarn=ref("%s-arn" % kwargs["action"]["name"])
            eventsource=fn_getatt(kwargs["name"], "StreamArn")
            props={"FunctionName": funcarn,
                   "EventSourceArn": eventsource,
                   "StartingPosition": "LATEST"}
            return "AWS::Lambda::EventSourceMapping", props
        return LambdaMapping(**kwargs)
    template=Template(resources=[Table(**kwargs)])
    if "action" in kwargs:
        actionarn=parameter("%s-arn" % kwargs["action"]["name"])
        template.setdefault("parameters", [])
        template["parameters"].append(actionarn)
        template["resources"].append(LambdaMapping(**kwargs))
    return template

if __name__=="__main__":
    pass
