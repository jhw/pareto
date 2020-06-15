#!/usr/bin/env bash

. app.props

if [ -z $1 ]
then
    echo "Please enter stage (dev|prod)"
    exit 1
fi

aws cloudformation describe-stack-resources --stack-name $AppName-$1 --query "StackResources[].{\"1.Timestamp\":Timestamp,\"2.LogicalId\":LogicalResourceId,\"3.PhysicalId\":PhysicalResourceId,\"4.Type\":ResourceType,\"5.Status\":ResourceStatus}"
