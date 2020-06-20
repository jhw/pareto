### short [preprocessor]

- consider renaming func as action
- refactor preprocessor notes
- add trigger permissions
- add polling permissions

- add back sqs batch parameter
- bubble up `s3:ObjectCreated:*`, `NEW_IMAGE` etc to surface

### medium

- is sqs batch size really listed in the right place ?
- allow multiple event source mappings
- normalise ddb field names
- limit permissions and event source maps to specific functions only
- use logical/physical_id reference names
- preprocessor json schema
- aws scripts to support missing attributes
- check all scripts work on malformed stacks
  - delete_stack fails on missing S3 bucket
  - delete_stack doesn't appear to log IAM role deletion
- scaffold generator [notes]
- replace timestamp with git version
  - deploy LATEST unless commit specified
- installation of pip library dependencies
  
### thoughts

- find all tests rather than just index.py ?
  - conventions should be that all tests are in index.py
- check slow_russian version of deploy_stack.py
  - other stuff you could usefully pillage ?
- remove managed policy support ?
  - no might be useful
- queue batch size to be nested under function ?
  - feels like over- optimisation
- remove `-dashboard-` from dash name ?
  - too much hassle to allow dash to work without a name
- scripts to ping lambda, check logs ?
  - not really required as this is about deployment not runtime
  
### long

- sns
- dead letter queues
- layers
- dashboard section titles
- queue, table charts

- CI pipeline (codepipeline, codebuild)

- groups [notes]
- github actions for lambda push
- slack alerts
- cognito
- route 53
- cloudfront

- ec2, codedeploy

### done

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
