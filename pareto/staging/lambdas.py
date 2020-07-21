import datetime, re, unittest

class LambdaCommit(dict):

    @classmethod
    def parse(self, s3key):
        key=LambdaCommit()
        tokens=s3key.split("/")
        key["app"]=tokens[0]
        key["name"]=tokens[2]
        tokens=tokens[-1].split(".")[0].split("-")
        key["hexsha"]=tokens.pop()
        key["timestamp"]=datetime.datetime(*[int(tok) for tok in tokens])
        return key

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
                self+=[obj["Key"] for obj in struct["Contents"]]

    @property
    def groups(self):
        keys={}
        for s3key in self:
            key=LambdaCommit.parse(s3key)
            keys.setdefault(key["name"], {})
            keys[key["name"]][key["hexsha"]]=s3key
        return keys
                
    @property
    def latest(self):
        keys={}
        for s3key in sorted(self):
            key=LambdaCommit.parse(s3key)
            keys[key["name"]]=s3key
        return keys

class LambdaCommitTest(unittest.TestCase):

    App="my-app"
    Name="hello-world"
    Timestamp=datetime.datetime(*[1970, 12, 20, 19, 30, 0])
    Hexsha="ABCDEFGH"

    Key="my-app/lambdas/hello-world/1970-12-20-19-30-00-ABCDEFGH.zip"
    
    def test_new(self):
        key=LambdaCommit(**{attr: getattr(self, attr.capitalize())
                         for attr in ["app", "name", "timestamp", "hexsha"]})
        self.assertEqual(str(key), self.Key)

    def test_parse(self):
        key=LambdaCommit.parse(self.Key)
        for attr in ["app", "name", "timestamp", "hexsha"]:
            self.assertEqual(key[attr], getattr(self, attr.capitalize()))
            
if __name__=="__main__":
    unittest.main()
