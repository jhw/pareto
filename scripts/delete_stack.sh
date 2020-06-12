#!/usr/bin/env bash

. app.props

aws cloudformation delete-stack --stack-name $AppName
