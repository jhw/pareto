#!/usr/bin/env python

import unittest

from tests.staging.lambdas import LambdaKeyTest

Tests=[LambdaKeyTest]

def run_tests(config):
    suite=unittest.TestSuite()
    for test in Tests:
        suite.addTest(unittest.makeSuite(test))
    runner=unittest.TextTestRunner()
    runner.run(suite)

if __name__=="__main__":
    run_tests(config={})

