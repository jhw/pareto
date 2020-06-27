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
    """
    - don't *think* you need a LambdaPermission if you have a LambdaMapping
    - (think LambdaPermission is only for primitives without EventSourceMapping, ie S3, SNS)
    - no BatchSize ?
    """
    def LambdaMapping(**kwargs):
        suffix="%s-mapping" % kwargs["action"]["name"]
        @resource(suffix)
        def LambdaMapping(**kwargs):
            funcname=fn_getatt(kwargs["action"]["name"], "Arn")
            eventsource=fn_getatt(kwargs["name"], "StreamArn")
            props={"FunctionName": funcname,
                   "EventSourceArn": eventsource,
                   "StartingPosition": "LATEST"}
            return "AWS::Lambda::EventSourceMapping", props
        return LambdaMapping(**kwargs)
    resources=[Table(**kwargs)]
    if "action" in kwargs:
        resources.append(LambdaMapping(**kwargs))
    return {"resources": resources}

if __name__=="__main__":
    pass
