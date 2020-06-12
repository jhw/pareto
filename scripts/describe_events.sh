#!/usr/bin/env bash

. app.props

if [ -z $1 ]
then
    echo "Please enter stage (dev|prod)"
    exit 1
fi

aws cloudformation describe-stack-events --stack-name $AppName-$1 --query "StackEvents[].{\"1.Timestamp\":Timestamp,\"2.Id\":LogicalResourceId,\"3.Type\":ResourceType,\"4.Status\":ResourceStatus,\"5.Reason\":ResourceStatusReason}"
