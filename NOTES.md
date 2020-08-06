### cors testing 6/8/20

- https://stackoverflow.com/questions/43871637/no-access-control-allow-origin-header-is-present-on-the-requested-resource-whe

### single quotes rendering 6/8/20

- https://stackoverflow.com/questions/37094170/a-single-string-in-single-quotes-with-pyyaml
- problem is some cors strings need to be encoded with very specific quotes eg "'foobar'"
- but pyyaml will render "'foobar'" as '''foobar'''
- ruamel.yaml will solve this
- https://pypi.org/project/ruamel.yaml/
- but do you want to replace your core yaml parser
- might be better to hack it
- see dev/yaml_single_quotes.py

### singletons 6/8/20

- maybe singletons doesn't need a decorator
- maybe instead you get singleton behaviour by defining different types
- eg a user pool, defined as a type, is a singleton
- so the ref mechanism becomes all important
- can the ref mechanism be made generic if you have more refs than simply actions ?
- layers would be good candidate for a separate type
- api cors options would probably not as currently depends on a specific method type

### polyreader non functionals 6/8/20

- cloudfront and route 53
- google federated login
- chrome link importer
- landing page / email harvester (webflow?) 
- stripe and pricing 

### checking of output refs 5/8/20

- something which uses fn:getatt and `Outputs.XXX` as the second arg is a dfferent kind of beast to standard arg checking which checks the first argument (the reource)
- this time it's an attribute name, similar to arn
- therefore needs its own checking
- which is actually done at the env level

### singletons 5/8/20

- can think of a number of examples of useful singletons
- layers, api gateway logging, iam roles, user pools
- key is probably that they are not bound to a particular name specified in the dsl
- which means you might have an @singleton decorator similar to @resource
- which probably means @resource should be simplified
- the nice thing is you can add multiple singletons to the list of resources and they will still be resolved to a single resource because of the conversion from list of tuples to dict

### nested stack parameters 3/8/20

- trigger stacks may require action arns output from actions template
- should be able to hack via naming convention
- iterate across trigger templates
- if template defines arn parameter, create nested template parameter for that parameter, pointed at the actions template
- then extend to do proper lookup of all sources and destinations of different params

### first class actions 2/8/20

- actions should be first class components
- then trigger can use reference to them
- in fact two triggers could then reference the same action
- means dashboards should probably be separate template, so remove them for the time being
- don't need to export non-action arns
- but triggers will need action arn parameters
- if a trigger has an action then it adds the permission/mapping to go with that arn
- as temporary measure, import any function arns defined as parameters from the actions template
- as a more complex step could have a template factory which produces templates sized within the constraints
- then need a more complex parameter assignment layer

### layout 31/7/20

- think have over- optimised the layout
- that is, nesting actions and dashes within triggers layouts and having no template parameters
- a decent layout manager would manage the template parameters for you
- so think thus far have over- optimised and am missing the layout management layer
- can feel this in the code smell around synth_action and the difficulty of seeing how the auth template will fit it (requires parameter exports)
- so roll back to a system in which you have a separate actions template and also a separate dashes template
- as you iterate through dsl groups, add action to actions template if exists
- actions always export arns
- triggers need to use references to arn action parameters rather than internally generated arns
- key is to understand that dsl structure doesn't have to be the same as layout
- and in particular layout should probably be flatter to give you more options
- all the dashboard class stuff is over- optimisation

### cognito 29/7/20

- see latest gists
- really only relates to apis
- so include as part of api
- initially just create a very basic pool
- actually no this isn't going to work
- really need to create a singleton pool
- but then refs to that pool need to be exported from auth stack and imported into apis stack
- so how is that going to work without complexity overkill ?

### layers 26/7/20

- add layer staging to deploy_stack.py
- create layer component
- action to include layer references
- add support for layers as arns

### dashboards 25/7/20

- dashes are being done wrongly
- If u aggregate if a single template u risk bottleneck, also over complexity
- Would be much better if each type had its own dashboard 
- So template class, in addition to Params/resources/outputs, also has an instance of dashboard class
- In fact you could create classes for Params, resources, outputs and dashboard
- Each has merge/update and render methods 
- But first three are just lists 
- Dash is more complex because must be aggregated under a single dashboard resource 
- And rendering is probably the stuff which includes all the x and y methods 
- Means the dashboard class and chart fixtures probably disappear
- You might have an ActionChart class/function
- Then instances of that for all the common functions 
- maybe template, env etc need to live in Pareto root
- And then you have a new charts directory 
- Certainly feels like template needs to be beefed up to include dash rendering capabilities 
- Then feels like it also needs unit tests

### general 25/7/20

- move staging tests into root tests directory so don’t have to include moto in pip dependencies 
- Add dependencies to setup.py
- Make project public again
- Deployment of index.json / ui
- output arns of actions and triggers
- list outputs option to ignore all arns 

### targets 24/7/20

- right now you have "Resource: *" in aws policy document
- so this means an action can ping any trigger for which it has resource permissions
- but if you included target information in dsl then you could lock stuff down to one particular resource
- but need to consider carefully as will likely mean increased headache of exporting and importing function arns around the place
- actually it's worse than that as you need to export the trigger arns

### nested actions 23/7/20

- target is definitely over optimisation and needs to be removed
- if you bind actions to triggers then each action can request very specific look back permissions
- if Iam is simplified and you no longer need to remap triggers then feels like preprocessor fades away and is maybe only used for name validation
- function filtering should also fade away since every trigger can potentially include a function
- but do u really want separate dashboards for each trigger type?
- probably yes you do
- actions no longer need unique names, they can take names of parent triggers
- but should probably use a function suffix
- check how api does it
- api is the model for all other triggers
- consider it an externally pinged trigger 

### nested actions 23/7/20

- all actions to be nested under trigger types ?
- dedicated action type should disappear
- similar to how apigw+function works
- the other thing that this would help a lot with is importing/exporting of function references across templates when creating master template
- and no more parameter creation when for function arns; instead you could revert back to using locally created arns
- will clearly require action to be available to all (trigger) components
- is basically the extension of the api model to all triggers
- api is now just api gateway bound to a function, just the same way any old trigger can be bound to a function
- so there's a nice symmetry there
- essentially function and iam stuff need to be available component root
- the other thing this fixes is the complexity of the trigger/target model
- if you bind a trigger and an action together then you can automatically include any lookback permissions you need within that particular component
- so then any target iam permissions should probably just be specified within the top level dsl
- which means you can really do away with the whole trigger/target model :)

### type hardcoding 23/7/20

- pareto/scripts/__init__.py [filter_functions]
- pareto/components/env.py [dashboard filtering]
- pareto/components/dashboard.py

### dynamic pythonpath 23/7/20

- set pythonpath dynamically from globals["src"]
- https://stackoverflow.com/questions/3108285/in-python-script-how-do-i-set-pythonpath/3108301
- affects push_lambdas.py, test.py
- test.py needs to load config
- changing lambda source then causes push_lambdas.py to fail

### layers 23/7/20

- add nested lambda key to staging
- change lambda staging so leaf values are objects not strings
- add sample layer config to hello.yaml
- add layer staging to deploy_stack.py
  - validate layer exists in s3
  - leaf objects as per lambdas
- new layer component in functions
- create layer component if layer config exists
- add support for layer arns

### layers 20/7/20

- add layer staging hook into deploy_stack.py
- add simple layer name to config
- basic layer component
- create layer when name exists, with runtime
- add arn reference to layer in function
- add layer versioning
- allow layers to be specified by arn, in which case layer object not created

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
