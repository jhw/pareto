#!/usr/bin/env python

import unittest

from pareto.scripts.helpers.profiles import toggle_aws_profile

from tests.staging.lambdas import LambdaKeyTest, LambdaKeysTest

Tests=[LambdaKeyTest,
       LambdaKeysTest]

@toggle_aws_profile
def run_tests(config):
    suite=unittest.TestSuite()
    for test in Tests:
        suite.addTest(unittest.makeSuite(test))
    runner=unittest.TextTestRunner()
    runner.run(suite)

if __name__=="__main__":
    run_tests(config={})

