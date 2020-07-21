import datetime, re, unittest

class LambdaCommit(dict):

    @classmethod
    def parse(self, key):
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
                self+=[LambdaCommit.parse(obj["Key"])
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
    
    def test_new(self):
        commit=LambdaCommit(**{attr: getattr(self, attr.capitalize())
                               for attr in ["app", "name", "timestamp", "hexsha"]})
        self.assertEqual(str(commit), self.Key)

    def test_parse(self):
        commit=LambdaCommit.parse(self.Key)
        for attr in ["app", "name", "timestamp", "hexsha"]:
            self.assertEqual(commit[attr], getattr(self, attr.capitalize()))
            
if __name__=="__main__":
    unittest.main()
