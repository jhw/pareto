import datetime, re, unittest

class LambdaKey(dict):

    @classmethod
    def parse(self, s3key):
        key=LambdaKey()
        def pop_timestamp(tokens):
            ts=[int(tokens.pop())
                for i in range(6)]
            ts.reverse()
            return datetime.datetime(*ts)
        tokens=s3key.split("/")
        key["app"]=tokens[0]
        tokens=tokens[-1].split(".")[0].split("-")
        key["hexsha"]=tokens.pop()
        key["timestamp"]=pop_timestamp(tokens)
        key["name"]="-".join(tokens)
        return key

    def __init_(self, kwargs={}):
        dict.__init__(self, kwargs)

    def __str__(self):
        def format_timestamp(value):
            if isinstance(value, datetime.datetime):
                return value.strftime("%Y-%m-%d-%H-%M-%S")
            else:
                return re.sub("\\W", "-", str(value))
        return "%s/lambdas/%s-%s-%s.zip" % (self["app"],
                                            self["name"],
                                            format_timestamp(self["timestamp"]),
                                            self["hexsha"])
    
class LambdaKeys(list):

    def __init__(self, config, s3):
        list.__init__(self)
        paginator=s3.get_paginator("list_objects_v2")
        pages=paginator.paginate(Bucket=config["globals"]["bucket"],
                                 Prefix="%s/lambdas" % config["globals"]["app"])
        for struct in pages:
            if "Contents" in struct:
                self+=[obj["Key"] for obj in struct["Contents"]]
                
    @property
    def latest(self):
        keys={}
        for s3key in sorted(self):
            key=LambdaKey.parse(s3key)
            keys[key["name"]]=s3key
        return keys

    @property
    def commits(self):
        keys={}
        for s3key in self:
            key=LambdaKey.parse(s3key)
            keys.setdefault(key["name"], {})
            keys[key["name"]][key["hexsha"]]=s3key
        return keys

class LambdaKeyTest(unittest.TestCase):

    App="my-app"
    Name="hello-world"
    Timestamp=datetime.datetime(*[1970, 12, 20, 19, 30, 0])
    Hexsha="ABCDEFGH"

    Key="my-app/lambdas/hello-world-1970-12-20-19-30-00-ABCDEFGH.zip"
    
    def test_new(self):
        key=LambdaKey(**{attr: getattr(self, attr.capitalize())
                         for attr in ["app", "name", "timestamp", "hexsha"]})
        self.assertEqual(str(key), self.Key)

    def test_parse(self):
        key=LambdaKey.parse(self.Key)
        for attr in ["app", "name", "timestamp", "hexsha"]:
            self.assertEqual(key[attr], getattr(self, attr.capitalize()))
            
if __name__=="__main__":
    unittest.main()
