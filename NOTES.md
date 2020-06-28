### lookback permissions 28/6/20

- required for event sourcing which under the hood is really doing polling :-/
- but then so does Kafka lol

- "dynamodb:GetRecords"
- "dynamodb:GetShardIterator"
- "dynamodb:DescribeStream"
- "dynamodb:ListStreams"
- "sqs:ReceiveMessage"
- "sqs:DeleteMessage"
- "sqs:GetQueueAttributes"

### CI pipeline 28/6/20

- start with basic codepipeline/codebuild routine
- problem will be lambda deployment
- certainly if it's git based it won't work as the codebuild env isn't git based
- feels like you may need a script to assemble a yaml file saying which lambdas you want deployed, which could then be manually adjustable
- also you're not going to be able to deploy lambdas from this script as again you don't have git commit versions
- so really need github actions to be pushing lambdas on commit
- then codebuild script could probably iterate across all deployments and find latest, unless there is some file saying which manual ones to use

### layers 28/6/20

- maybe each layer should contain a single package with a single version
- since you can have multiple layers for each function
- would be consistent with python's "import x, import y" philosphy

### sqs partitioning 27/6/20

- think sqs partitioning will work fine
- single queue
- queue event mapping batch size set to 1
- batch all items for a given league within a single record
- don't set function concurrency
- you should still get parallel execution

### action targets 19/6/20

- cf non- event sourced triggers (sns, s3, cloudwatch events) explictly nest actionreferences under trigger
- but that's not how you design lambdas, which are action- centric but where you need info regarding the trigger (event)
- so makes sense for dsl to nest triggers under actions
- primary purpose of pre-processor is to remap actions nested triggers into triggers nested actions
- secondary purpose is permissions layer
- permissions layer is three- fold
- firstly any non- event sourced trigger will need an explicit resource permission to invoke lambda
- but this is handled under the hood by pareto components
- secondly an action may need permissions call other services
- these other services may be trigger related or not (polly, translate)
- you could specify them all under permissions at the dsl level
- but shouldn't the pre-processor be able to infer the trigger related permissions ?
- feels like action should contain (optinal) target as well as trigger
- target can be used to infer permissions action needs for other triggers
- will also help to infer chain if you ever get round to charting (right now not possible without target)


### skeleton generator 14/6/20

- feels like there is a room for a skeleton generator
- use jinja2 templates
- create individual index.py, test.py
- then create global test.py function
- functions could have mock parameter which specifies what moto mock stuff is set up for them
- then you could include all the sample events in them

### groups 14/6/20

- feels like ultimately you will bump up again limits
- so probably need nested stacks to extend scale
- but what groups of stuff to choose ? not clear

### classes 14/6/20

- what if you want to defined mappings at the function level ?
- that's probably okay in most cases because a mapping is an independent entity from an event source
- at least for sqs, ddb, kinesis
- but not for s3, sns
- where a function would have to go and modify the bucket
- and not sure it's helped if you decide all notifications have to happen via sqs
- feels like you need a class where you could `addS3Notification()` etc
