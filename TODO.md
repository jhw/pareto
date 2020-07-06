### short

- avoid filtering for functions at env/dashboard level ?
- harmonise s3 lambda, template paths
  - remember lambda path should not include stage name

- adapt inspection scripts for multiple stacks

### medium

- better ways of handling app/stage/region/bucket props ?

- layers [notes]
- secrets manager
- replace timestamp with git version
- scaffold generator [notes]
- sns topics
- cloudwatch alerts
- preprocessor json schema
- pip dependency installation

### v1.1

- CI pipeline [notes]
- sqs fifo
- topology chart generation
- custom lambda authorisers
- cognito
- route 53
- appsync/graphql
- cloudfront

### thoughts

- aggregate IAM roles ?
  - doesn't seem worth it when unlikely to be template size constraint
- consider converting Template to extend object not dict ?
  - no point
- investigate template usage of lists of tuples (dicts ?)
  - no is fine
- refactor env.py so each function returns a template/templates ?
  - no is fine
- multiple sqs actions ?
  - i think leave it as single action for time being for simplicity
- add outputs support to fn::getatt ? option to bypass logical_id ?
  - think it's simpler just to have special function in master template
- refactor env to use Master function and don't have it attach directly ?
- preprocessor unit tests ?
  - probably not worth it at this stage, assuming it all compiles
- iam role pool to reduce template size ?
  - not going to reduce template size meaningfully
  - also feels like an over- optimisation
- don't put blank subs {} ?
  - doesn't work - needs blank
- preprocessor circularity detection ?
  - trig!=target unless s3 bucket, in which case paths can't be the same
  - just too meta for now
- separate functions for arn creators if they can't work on a single line
- eliminate `:::` in S3 bucket policy ?
  - no, seems to be standard case
  - https://docs.aws.amazon.com/AmazonS3/latest/dev/example-bucket-policies.html
- use ${AWS::Region} ?
  - no; dash will never support it as supposed to be multi- region
- convert underscored table attribute names to hashes ?
  - no; you don't do this for any other names so why bother with table ?
- find all tests rather than just index.py ?
  - conventions should be that all tests are in index.py
- remove managed policy support ?
  - no might be useful
- remove `-dashboard-` from dash name ?
  - too much hassle to allow dash to work without a name
- scripts to ping lambda, check logs ?
  - not really required as this is about deployment not runtime
  
### done

- simplify master stack params, output creation

```
Template error: instance of Fn::GetAtt references undefined resource HelloAction2
```

- *** s3 event notifications are still using direct function arn refs rather than refs to params ***

- json templates not yaml :-)
- access denied error
  - do s3 templates exist ?
- weird that doesn't include triggers stack
- remove empty templates ?
- bad cloudformation ref
- master outputs must be nested under value
- outputs ref to be part of attr not stack name
- add back stack dumping
- add back deployment script
- fix back refs to Config
- template push
- add back metrics
- add metrics alerts
- add back lambda push
- add back lambda testing
- simplify dashboard marshalling
- dashboard to filter for the existence of functions
- dashboard stack
- refactor creation of api/action/trigger stacks as per master
  - avoid popping components
- pass config, templates to init_template
- simplify env.py creation
  - avoid popping components from config
- add local copies of synth_template and rename as init_template
- see if you can remove dict from render method
- add render method to template
- stack to return template
- remove trim method from template
- synth_template should use Template class
- move synth_template into env
- add Template class
- remove trim_template
- pop outputs so internal ones are not exposed publically
- include aggregated outputs in master stack
- add per- stack parameters
- filter outputs from each component group {name: stack}
- trim() decorator to remove empty params/resources/outputs
- stack for each component group
- stack url
- pass parameters to stack
- stack needs its own component
- when creating environment need to use synth_template(config) etc
- stack needs to become environment
- convert remaining trigger arns to parameters and refs
- convert local ARN lookups to parameter refs
- sample parameter
- pass components to template
- generate and save mutiple stacks
- add dashboard stack
- add master stack
- stack type filters
- rename stack as template
- new stack file which creates multiple templates
- comment out deployment
- remove metrics
- remove dashboard
- ensure all yaml dumping done without refs
- raw stack is missing iam permissions
  - but works when u run preprocessor from the command line
- dump raw, cooked templates
- iam/permissions is nested incorrectly
- preprocessor demo.yaml sample
- integrate preprocessor via decorator
- force depends to be a list
- remove iam compaction
  - check iam uses set
- lambda retry behaviour
  - https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-lambda-eventinvokeconfig.html
- export important ARNs/refs
- preprocessor to include sqs by default for dlq
- dead letter queues
- rename stack.yaml as demo.yaml
- note and remove specific iam support

```
2020-06-27 13:32:16.383000+00:00		HelloTableHelloGetMapping		AWS::Lambda::EventSourceMapping		Cannot access stream arn:aws:dynamodb:eu-west-1:119552584133:table/pareto-demo-hello-table-dev/stream/2020-06-27T13:31:43.497. Please ensure the role can perform the GetRecords, GetShardIterator, DescribeStream, and ListStreams Actions on your stream in IAM. (Service: AWSLambda; Status Code: 400; Error Code: InvalidParameterValueException; Request ID: 08979523-6e69-425a-88bf-13772486119b)
```

```
2020-06-27 13:35:48.379000+00:00		HelloQueueHelloGetMapping		AWS::Lambda::EventSourceMapping		The provided execution role does not have permissions to call ReceiveMessage on SQS (Service: AWSLambda; Status Code: 400; Error Code: InvalidParameterValueException; Request ID: 9e0c49ef-e60f-45de-a789-dc6ce39ff196)
```

- capture precise ddb, sqs actions required for lookback
- aws scripts to support missing attributes
- add S3 AccountId
- better decorator handling in logical id formatting of depends
- depends should be automatically converted to logical id
- refactor global_name as resource_id
- new logical_id wrapper for hungarorise
- https://aws.amazon.com/premiumsupport/knowledge-center/unable-validate-circular-dependency-cloudformation/
- deployment fails if no outputs (eg bucket (no website) and function)
- comment out bucket sourcearn
- check all scripts work on malformed stacks
  - delete_stack fails on missing S3 bucket
  - delete_stack doesn't appear to log IAM role deletion
- eliminate ${AWS::Partition}
- use `fn::sub` in bucket policy creation
- replace :aws: with :${AWS::Partition}
- harmonise `Allow` vs `allow`
- remove `Sid`
- https://docs.aws.amazon.com/apigateway/latest/developerguide/arn-format-reference.html
- https://docs.aws.amazon.com/lambda/latest/dg/services-apigateway.html

```
$ aws lambda add-permission --function-name my-function \
--statement-id apigateway-get --action lambda:InvokeFunction \
--principal apigateway.amazonaws.com \
--source-arn "arn:aws:execute-api:us-east-2:123456789012:mnh1xmpli7/default/GET/"
```

- the number is the account number, so can maybe be ignored
- test dashboard yaml
  - doesn't work
- s3, cloudwatch event permission source
- comment out temp code in stack.yaml
- re- test stack.yaml deployment
- expose lambda options to dsl
  - audio generator will require concurrency
- add unique name testing
- embed validation in wrapper method
- abstract iam class
- abstract iam methods used by action
- allow api to add dest permissions
- allow preprocessor target to be optional
- change wildcard name to expand
- only add wildcard if no colon in name
- add render method to iam to convert to list
- add flatten method to iam which removes specifics if wildcard exists
- move attach decorator
- move wildcard decorator
- default logs permission
- move wildcard function to iam class
- avoid duplicating permissions
- add iam wildcard
- arg parameters
  - s3:ObjectCreated:*
  - NEW_IMAGE (ddb)
- test optional args
- sqs batch size
- trigger, target permissions
- batch handling
- add target info to slow russian
- validate and clean up targets
- bucket website
- eval() test
- replace func type with separate api, action types
  - nest/hide api method field
- refactor preprocessor notes
- don't pop binding so u don't have to pass it
- rename self as trigger
- rename func as action
- rename target as action in main pareto body
- rename nonfunc as trigger
- rename src ac trigger
- refactor target references
  - should be popped from nonfuncmap
  - if necessary should be augmented by src/dest args [path]
  - remove need to sent 3rd arg to `add_xxx_target`
  - this is linked to the problem of queue batch not appearing at the right nesting level
- nest `target` with `name`, `batch`
- replace event source `function` with `target`
- add function permissions based on target (s3, ddb, queue)
- pass thru custom permissions
- check existing permissions before adding
- initialise permissions
- table schema
- queue batch
- functions with name `audio`, `content` look incorrect
- aggregate type/name keys
- validate uniqueness
- validate sources
- allocate sources to components and render
- ddb, sqs permissions
- bucket website support
- slow russian stack.yaml
- remove ddb/sqs permissions, redeploy
- list_failures.py
- add logger to stack deletion
- all scripts to capture client error
- delete_stack.py
  - empty buckets
  - detach IAM policies
  - capture waiter error
- change all scripts to use __init__.py
- move deploy code into scripts/__init__.py
- describe_outputs.py
- describe_stacks.py
- describe_events.py
- describe_resources.py
- deployment logger
- capture waiter error
- limit calculations
- separate get, post lambdas
- common helpers
  - filtering of functions from components
  - replacement of "-" with "_" in function name
- move scripts to pareto/scripts
- charts/functions/README
- toggle google before running tests
- run tests
- sample test file
- push_lambda to iterate over directory contents
- replace s3 bucket/key parameters with hardcoded values
- replace lambdakeys with config augmented by s3 bucket, key
- dump stack
- abstract timestamp
- push_lambda to check directory exists
- generate lambda keys by iterating over functions
- synth stack internally
- make Config static and avoid passing it round
- lambda key to be full s3key
- pass a dict of lambda keys, with function name
- stack create vs update
  - call describe stacks and see if it exists
- s3 upload failing
  - deploy.sh bytes => local 488 / remote 488
  - deploy.py bytes => local 436 / remote 360
- deploy stack and wait
- separate zfname from zipping
- python lambda deployment
- queue event mapping
- table event mapping
- s3 notifications
- table indexes
- table

```
 2020-06-13T05:11:13.573Z|  Table                   |  AWS::DynamoDB::Table        |  CREATE_FAILED                                |  One or more parameter values were invalid: Some AttributeDefinitions are not used. AttributeDefinitions: [my-string, my-int, my-hash], keys used: [my-hash, my-string] (Service: AmazonDynamoDBv2; Status Code: 400; Error Code: ValidationException; Request ID: VB2Q7GALG1S0RNLD0LPL6E6KHFVV4KQNSO5AEMVJF66Q9ASUAAJG)   |
```

- timer
- queue
- refactor DependsOn handling
  - avoid `len(props) > 2`
- add api gateway output to sample lambda
- test api gateway
- bad gateway rest api ref
- fix bad ref to Deployment
- api gateway DependsOn
  - needs to be returned as an (optional) third arg alongside Type, Properties
- move templates, lambda to tmp
- dash needs with and height parameters
- check dashboard
- role policy doc error
- deploy
- deploy script to push lambda
- deploy script to pass parameters
- configure function in demo.yaml
- index.py
- website
- test bucket deployments
- add stage name to all sh scripts
- remove blank outputs, parameters
- only add dashboard if not blank
- synth_stack.py to read config
- script to deploy stack
- stack.yaml
- script to generate stack
- setenv.sh
- pip packaging
