### short [deploy-stack]

- s3 upload failing
  - deploy.sh bytes => local 488 / remote 488
  - deploy.py bytes => local 436 / remote 360

- stack create vs update
- handle waiter error
- lambda directories
- GET, POST lambdas
- unit tests
- replace timestamp with git version
- deploy LATEST unless commit specified

### medium

- move scripts to pareto/scripts

- delete_stack.py
  - empty buckets
  - detach IAM policies

- generate stack as part of deploy script
  - remove params passed to script

### validation

- unique names
- functions references
- functions mapped to ddb streams to include ddb in role permissions
  - ditto sqs
- regex permission format

### thoughts

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
- limit calculations
- dashboard section titles
- skeleton generator
- queue, table charts
- slack alerts
- nested stacks
- CI pipeline (codepipeline, codebuild)
- github actions for lambda push
- cognito
- route 53
- cloudfront
- ec2, codedeploy

### done

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
