#!/usr/bin/env python

import unittest

from pareto.staging.lambdas import LambdaCommitTest, LambdaCommitsTest
from pareto.staging.layers import LayerPackageTest, LayerPackagesTest

Tests=[LambdaCommitTest,
       LambdaCommitsTest,
       LayerPackageTest,
       LayerPackagesTest]

if __name__=="__main__":
    suite=unittest.TestSuite()
    for test in Tests:
        suite.addTest(unittest.makeSuite(test))
    runner=unittest.TextTestRunner()
    runner.run(suite)


