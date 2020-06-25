API Gateway SourceArn for Lambda Permission ?

I'm trying to put an (HTTP) API Gateway on top of a Lambda function (see full Coloudformation below)

The API Gateway needs an `AWS::Lambda::Permission` resource in order to be able to execute the Lambda.

Everything works fine provided the `SourceArn` parameter is _not_ set, but I'd like to include it for extra security.

In most event- driven cases this is easy because you have a single event trigger resource (`AWS::S3::Bucket`, `AWS::SNS::Topic`) and it's simple to get an Arn using `Fn::GetAtt`.

But API Gateway seems different, you have to assemble the Arn by hand :-(

- https://docs.aws.amazon.com/lambda/latest/dg/services-apigateway.html

```
$ aws lambda add-permission --function-name my-function \
--statement-id apigateway-get --action lambda:InvokeFunction \
--principal apigateway.amazonaws.com \
--source-arn "arn:aws:execute-api:us-east-2:123456789012:mnh1xmpli7/default/GET/"
```

So I've added the following snippet to the `AWS::Lambda::Permission` which looks fine / deploys fine, but then gives me `HTTP 500` `Internal Server Error` when I actually ping the endpoint :-(

```
Resources:
  {...}
  HelloGetApiGwPermission:
    Properties:
      {...}
      SourceArn:
        Fn::Sub:
        - arn:aws:execute-api:eu-west-1:${AWS::AccountId}:${rest_api}/dev/
        - rest_api:
            Ref: HelloGetApiGwRestApi
```

What's the correct `SourceArn` format should be here to make this work ?

---

[full stack]

```
Resources:
  {...}
  HelloGet:
    Properties:
      Code:
        S3Bucket: my-staging-bucket
        S3Key: foobar-demo/hello-get-2020-06-25-06-10-16.zip
      FunctionName: foobar-demo-hello-get-dev
      Handler: index.handler
      MemorySize: 512
      Role:
        Fn::GetAtt:
        - HelloGetRole
        - Arn
      Runtime: python3.7
      Timeout: 30
    Type: AWS::Lambda::Function
  HelloGetApiGwDeployment:
    DependsOn:
    - HelloGetApiGwMethod
    Properties:
      RestApiId:
        Ref: HelloGetApiGwRestApi
    Type: AWS::ApiGateway::Deployment
  HelloGetApiGwMethod:
    Properties:
      AuthorizationType: NONE
      HttpMethod: GET
      Integration:
        IntegrationHttpMethod: POST
        Type: AWS_PROXY
        Uri:
          Fn::Sub:
          - arn:${AWS::Partition}:apigateway:eu-west-1:lambda:path/2015-03-31/functions/${lambda_arn}/invocations
          - lambda_arn:
              Fn::GetAtt:
              - HelloGet
              - Arn
      ResourceId:
        Fn::GetAtt:
        - HelloGetApiGwRestApi
        - RootResourceId
      RestApiId:
        Ref: HelloGetApiGwRestApi
    Type: AWS::ApiGateway::Method
  HelloGetApiGwPermission:
    Properties:
      Action: lambda:InvokeFunction
      FunctionName:
        Fn::GetAtt:
        - HelloGet
        - Arn
      Principal: apigateway.amazonaws.com
    Type: AWS::Lambda::Permission
  HelloGetApiGwRestApi:
    Properties:
      Name: hello-get-api-gw-rest-api
    Type: AWS::ApiGateway::RestApi
  HelloGetApiGwStage:
    Properties:
      DeploymentId:
        Ref: HelloGetApiGwDeployment
      RestApiId:
        Ref: HelloGetApiGwRestApi
      StageName: dev
    Type: AWS::ApiGateway::Stage
  HelloGetRole:
    Properties:
      AssumeRolePolicyDocument:
        Statement:
        - Action: sts:AssumeRole
          Effect: allow
          Principal:
            Service: lambda.amazonaws.com
        Version: '2012-10-17'
      Policies:
      - PolicyDocument:
          Statement:
          - Action: logs:*
            Effect: Allow
            Resource: '*'
          Version: '2012-10-17'
        PolicyName: hello-get-policy
    Type: AWS::IAM::Role
```