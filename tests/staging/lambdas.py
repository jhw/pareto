from pareto.staging.lambdas import Lambda, Lambdas

import boto3, datetime, unittest

from moto import mock_s3

class LambdaTest(unittest.TestCase):

    App="my-app"
    Name="hello-world"
    Timestamp=datetime.datetime(*[1970, 12, 20, 19, 30, 0])
    Hexsha="ABCDEFGH"

    Key="my-app/lambdas/hello-world/1970-12-20-19-30-00-ABCDEFGH.zip"
    
    def test_create_s3(self):
        commit=Lambda.create_s3(self.Key)
        for attr in ["app", "name", "timestamp", "hexsha"]:
            self.assertEqual(commit[attr], getattr(self, attr.capitalize()))

    def test_str(self):
        commit=Lambda(**{attr: getattr(self, attr.capitalize())
                               for attr in ["app", "name", "timestamp", "hexsha"]})
        self.assertEqual(str(commit), self.Key)

@mock_s3
class LambdasTest(unittest.TestCase):

    Config={"globals": {"app": "my-app",
                        "bucket": "foobar"}}

    Keys=["my-app/lambdas/hello-world/1970-12-20-19-30-00-ABCDEFGH.zip",
          "my-app/lambdas/hello-world/1970-12-20-19-31-00-IJKLMNOP.zip",
          "my-app/lambdas/hello-world-2/1970-12-20-19-30-00-ABCDEFGH.zip"]
    
    def setUp(self):
        self.s3=boto3.client("s3")
        bucketname=self.Config["globals"]["bucket"]
        self.s3.create_bucket(Bucket=bucketname,
                              CreateBucketConfiguration={'LocationConstraint': 'EU'})
        for key in self.Keys:
            self.s3.put_object(Bucket=bucketname,
                               Key=key,
                               Body="{}")
        
    def test_latest(self):
        bucketname=self.Config["globals"]["bucket"]
        commits=Lambdas(self.Config, self.s3)
        latest=commits.latest
        for k, v in [("hello-world", "1970-12-20-19-31-00-IJKLMNOP.zip"),
                     ("hello-world-2", "1970-12-20-19-30-00-ABCDEFGH.zip")]:
            self.assertTrue(k in latest)
            self.assertTrue(str(latest[k]).endswith(v))

    def test_groups(self):
        bucketname=self.Config["globals"]["bucket"]
        commits=Lambdas(self.Config, self.s3)
        groups=commits.grouped
        for k, n in [("hello-world", 2),
                     ("hello-world-2", 1)]:
            self.assertTrue(k in groups)
            self.assertEqual(len(groups[k]), n)
        
    def tearDown(self):
        bucketname=self.Config["globals"]["bucket"]
        struct=self.s3.list_objects(Bucket=bucketname)
        if "Contents" in struct:
            for obj in struct["Contents"]:
                self.s3.delete_object(Bucket=self.Config["globals"]["bucket"],
                                      Key=obj["Key"])
        self.s3.delete_bucket(Bucket=bucketname)
                
if __name__=="__main__":
    unittest.main()
