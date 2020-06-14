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
