import datetime, re

class LambdaKey(dict):

    @classmethod
    def create_s3(self, key):
        commit=LambdaKey()
        tokens=key.split("/")
        commit["app"]=tokens[0]
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
        return "%s/lambdas/%s-%s.zip" % (self["app"],
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
                self+=[LambdaKey.create_s3(obj["Key"])
                       for obj in struct["Contents"]]

if __name__=="__main__":
    pass
