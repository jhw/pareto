#!/usr/bin/env bash

. app.props

aws cloudformation describe-stack-events --stack-name $AppName --query "StackEvents[].{\"1.Timestamp\":Timestamp,\"2.Id\":LogicalResourceId,\"3.Type\":ResourceType,\"4.Status\":ResourceStatus,\"5.Reason\":ResourceStatusReason}"
