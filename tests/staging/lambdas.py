from pareto.staging.lambdas import LambdaKey

import datetime, unittest

class LambdaKeyTest(unittest.TestCase):

    App="my-app"
    Timestamp=datetime.datetime(*[1970, 12, 20, 19, 30, 0])
    Hexsha="ABCDEFGH"

    Key="my-app/lambdas/1970-12-20-19-30-00-ABCDEFGH.zip"
    
    def test_create_s3(self):
        commit=LambdaKey.create_s3(self.Key)
        for attr in ["app", "timestamp", "hexsha"]:
            self.assertEqual(commit[attr], getattr(self, attr.capitalize()))

    def test_str(self):
        commit=LambdaKey(**{attr: getattr(self, attr.capitalize())
                            for attr in ["app", "timestamp", "hexsha"]})
        self.assertEqual(str(commit), self.Key)

if __name__=="__main__":
    unittest.main()
