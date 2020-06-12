### short

- s3 notifications

### medium

- refactor DependsOn handling
  - avoid `len(props) > 2`

- deploy_stack.py
  - handle multiple lambdas

- delete_stack.py
  - empty buckets
  - detach IAM policies

- cross validation of function refs
- unique name checking

- table
- queue
- timer

- table event mapping
- queue event mapping

- git- based python deployment

### thoughts

- remove `-dashboard-` from dash name ?
  - too much hassle to allow dash to work without a name
- scripts to ping lambda, check logs ?
  - not really required as this is about deployment not runtime
  
### long

- layers
- limit calculations
- dashboard section titles
- queue, table charts
- alerts
- CI pipeline (codepipeline, codebuild)
- cognito
- route 53
- cloudfront
- ec2, codedeploy

### done

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
