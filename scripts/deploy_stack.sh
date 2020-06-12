#!/usr/bin/env bash

. app.props

if [ -z $1 ]
then
    echo "Please enter stage (dev|prod)"
    exit 1
fi

timestamp=$(date +%Y-%m-%d-%H-%M-%S)
s3key=lambda-$timestamp.zip
zip $s3key index.py
aws s3 cp $s3key s3://$S3StagingBucket/$AppName/
aws cloudformation deploy --stack-name $AppName-$1 --template-file template-$1.yaml --parameter-overrides S3StagingBucket=$S3StagingBucket S3FunctionKey=$AppName/$s3key  S3LayerKey=undefined --capabilities CAPABILITY_NAMED_IAM
