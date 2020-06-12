#!/usr/bin/env bash

. app.props

if [ -z $1 ]
then
    echo "Please enter stage (dev|prod)"
    exit 1
fi

aws cloudformation deploy --stack-name $AppName-$1 --template-file template-$1.yaml --capabilities CAPABILITY_NAMED_IAM
