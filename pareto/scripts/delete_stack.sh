#!/usr/bin/env bash

. app.props

if [ -z $1 ]
then
    echo "Please enter stage (dev|prod)"
    exit 1
fi

aws cloudformation delete-stack --stack-name $AppName-$1
