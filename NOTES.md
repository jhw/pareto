### lambda staging 18/7/20

- does staging need to be refactored into two stage process in which staging keys are passed as parameters to templates ?
- This is certainly possible as staging variables don’t actually include the stage name 
- It also feels desirable as the current insertion of a staging attribute into kwargs feels like something of a hack
- But it also involves more complexity
- Because hard coded staging refs now have to be replaced with parameters and refs
- And because these are part of nested stacks these parameters now have to be declared as part of the master stack and then passed as args to nested stacks
- So you’re capping yourself at the max parameter level of 60 Params
- But given that each lambda requires at least 3-4 resources in total then you are still more likely to hit the 200 resource limit first
- And splitting things this ways isn’t really going to help with CI/cd because you still want to execute a single python script inside CodeBuild 
- You can’t generate list of staged files using one script and then pass to second script
- Because CodeBuild is bash not python
- And can’t really argue this helps logging because you can always log the currently staged variables 
- So overall it feels like this might be more trouble than it is worth
- can’t name a benefit other than “feels cleaner” (because marshalling of stage parameters doesn’t need stage name)
- But the suspect this is just replacing python staging of parameters with use of cloudformation parameter values
- Feels better because hardcoding == bad but in fact it’s just more complex

### components 14/7/20

```
pareto/components/preprocessor.py
pareto/components/dashboard.py
pareto/components/env.py
pareto/scripts/push_lambdas.py
pareto/scripts/deploy_stack.py
```

- preprocessor iterates through components, groups and modifies them
- but components container structure is left unchanged
- so will need to use map instead of list and in particular look for any filtering of components from list (is a proxy for map)
- dashboard filters function so will need to iterate through apis and actions instead
- env does various groupings of components so that will need to be eliminated
- scripts stuff uses filter_functions which will need to be eliminated
- maybe replace filter_functions with flatten_functions which appends actions and api groups together

### components 13/7/20

```
pareto/scripts/deploy_stack.py
pareto/scripts/push_lambdas.py
pareto/components/env.py
pareto/components/preprocessor.py
pareto/components/dashboard.py
```

- preprocessor currently picks items from the components list, remaps to groups and updates each component
- so components list is ultimately maintained
- dash iterates thru components and filters functions
- do you really want to unpack groups into a list and then regroup at the env level ?
- maybe is simpler to work with list internally, esp as you remap components ?
- so then it feels like the list representation is an intermediate layer; that the env is really a kind of post- processor; so that then it feels like the preprocessor layer is missing a pre- preprocessor which converts from a nice grouped format into a components list

### layers 9/7/20

- script to build single package layer
  - optional version
- layer component
  - pass layer runtime
- layer bucket, s3 key
  - including version
  - default LATEST
- function layer references
- deploy_stack.py to check layers exist
- managed layer support
  - don't create a layer if in arn format

### secrets 8/7/20

- hopefully shouldn't be too hard
- separate `secrets` attr in config
- add secrets to master stack
- nest JSON values if secret is complex
- err that's it

### API gateway stage names 7/7/20

- should apigw include stage that references stage name ?
- feels like it's intended for a single deployment with multiple stages
- but we have multiple deployments, one for each stage
- but unfortunately you need a stage as part of the apigw arn, eg
- arn:aws:execute-api:eu-west-1:${AWS::AccountId}:${rest_api}/dev/GET/
- however no need to hardcode it like this
- should use templating as `AWS::ApiGateway::Stage` has ref of `StageName` parameter (dev, prod)

### layer and iam pooling 6/7/20

- iam pooling seemed a nice idea but maybe not essential
- but difficulty is layers suffer from the same problem, but this time they are essential
- ie can't have each function having its own individual layers
- unless you decide on a single layer for all functions, containing all deps and forcing each function to take it
- well actually maybe unique layers aren't the worst way to go
- can treat them the same as optional IAM resources
- so for any function, specify a package layer with an optional version
- layers are specified on per- package, per version (optional) basis
- function component can create a layer resources if they are required, and then include the layer references within the function
- the layer resource will need to include a file reference in a commonly agreed format
- then u need a script to build the individual layers
- then deployment script will need to check that the layers actually exist
- and probably u need to test layers by including them within an index.py
- and don't forget u will need local dependencies to test
- then also need support for AWS layer ARNs (managed layers ?)

### master stack 5/7/20

- can you build master stack in the same way you do components, specifically using synth_template ?
- how does synth_template work ?
- you pass it a config of components, it iterates through them and generates each
- each component returns params, resources, outputs
- synth_template then aggregates these into a single template
- so this is very useful for building the underlying apis/actions/triggers template

### nested templates 29/6/20

- what would you need to do to get Pareto templates working ?
- Five templates - actions, apis, triggers, dashboards, master 
- Each will need Params section although maybe not master 
- Stack building process will need to build a series of different stacks 
- Dashboard needs separate api, actions and triggers dashes, all within dash template
- Each template will need to export arms and other stuff
- But actions will need to import trigger arns and vice versa 
- Any template which references an arn that is now part of another template will have to now use a parameter
- Deploy script will need to push stacks to s3
- Need new tested template component
- Then master template glues it all together 
- at heart this is a massive expansion of synth_stack

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
