#!/usr/bin/env python

import unittest

from pareto.scripts.helpers.profiles import toggle_aws_profile

from pareto.staging.lambdas import LambdaCommitTest, LambdaCommitsTest
from pareto.staging.layers import LayerPackageTest, LayerPackagesTest

Tests=[LambdaCommitTest,
       LambdaCommitsTest,
       LayerPackageTest,
       LayerPackagesTest]

@toggle_aws_profile
def run_tests(config):
    suite=unittest.TestSuite()
    for test in Tests:
        suite.addTest(unittest.makeSuite(test))
    runner=unittest.TextTestRunner()
    runner.run(suite)

if __name__=="__main__":
    run_tests(config={})

