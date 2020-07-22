import boto3, datetime, re, unittest

from moto import mock_s3

class LambdaCommit(dict):

    @classmethod
    def create_s3(self, key):
        commit=LambdaCommit()
        tokens=key.split("/")
        commit["app"]=tokens[0]
        commit["name"]=tokens[2]
        tokens=tokens[-1].split(".")[0].split("-")
        commit["hexsha"]=tokens.pop()
        commit["timestamp"]=datetime.datetime(*[int(tok) for tok in tokens])
        return commit

    def __init_(self, kwargs={}):
        dict.__init__(self, kwargs)

    def __str__(self):
        def format_timestamp(value):
            if isinstance(value, datetime.datetime):
                return value.strftime("%Y-%m-%d-%H-%M-%S")
            else:
                return re.sub("\\W", "-", str(value))
        return "%s/lambdas/%s/%s-%s.zip" % (self["app"],
                                            self["name"],
                                            format_timestamp(self["timestamp"]),
                                            self["hexsha"])
    
class LambdaCommits(list):

    def __init__(self, config, s3):
        list.__init__(self)
        paginator=s3.get_paginator("list_objects_v2")
        pages=paginator.paginate(Bucket=config["globals"]["bucket"],
                                 Prefix="%s/lambdas" % config["globals"]["app"])
        for struct in pages:
            if "Contents" in struct:
                self+=[LambdaCommit.create_s3(obj["Key"])
                       for obj in struct["Contents"]]

    @property
    def grouped_keys(self):
        keys={}
        for commit in self:
            keys.setdefault(commit["name"], {})
            keys[commit["name"]][commit["hexsha"]]=str(commit)
        return keys
                
    @property
    def latest_keys(self):
        keys={}
        for commit in sorted(self,
                             key=lambda x: x["timestamp"]):
            keys[commit["name"]]=str(commit)
        return keys

class LambdaCommitTest(unittest.TestCase):

    App="my-app"
    Name="hello-world"
    Timestamp=datetime.datetime(*[1970, 12, 20, 19, 30, 0])
    Hexsha="ABCDEFGH"

    Key="my-app/lambdas/hello-world/1970-12-20-19-30-00-ABCDEFGH.zip"
    
    def test_create_s3(self):
        commit=LambdaCommit.create_s3(self.Key)
        for attr in ["app", "name", "timestamp", "hexsha"]:
            self.assertEqual(commit[attr], getattr(self, attr.capitalize()))

    def test_str(self):
        commit=LambdaCommit(**{attr: getattr(self, attr.capitalize())
                               for attr in ["app", "name", "timestamp", "hexsha"]})
        self.assertEqual(str(commit), self.Key)

@mock_s3
class LambdaCommitsTest(unittest.TestCase):

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
        commits=LambdaCommits(self.Config, self.s3)
        latest=commits.latest_keys
        for k, v in [("hello-world", "1970-12-20-19-31-00-IJKLMNOP.zip"),
                     ("hello-world-2", "1970-12-20-19-30-00-ABCDEFGH.zip")]:
            self.assertTrue(k in latest)
            self.assertTrue(latest[k].endswith(v))

    def test_groups(self):
        bucketname=self.Config["globals"]["bucket"]
        commits=LambdaCommits(self.Config, self.s3)
        groups=commits.grouped_keys
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
