#!/usr/bin/env bash

aws cloudformation describe-stacks --query "Stacks[].{\"1.Name\":StackName,\"2.Status\":StackStatus}"
