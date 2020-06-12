#!/usr/bin/env bash

. app.props

aws cloudformation deploy --stack-name $AppName --template-file stack.yaml --capabilities CAPABILITY_NAMED_IAM
