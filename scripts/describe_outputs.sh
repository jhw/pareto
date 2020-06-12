#!/usr/bin/env bash

. app.props

if [ -z $1 ]
then
    echo "Please enter stage (dev|prod)"
    exit 1
fi

aws cloudformation describe-stacks --stack-name $AppName-$1 --query 'Stacks[0].Outputs' --output table
