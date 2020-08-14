import datetime, re

class Lambda(dict):

    @classmethod
    def create_s3(self, key):
        commit=Lambda()
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
    
class Lambdas(list):

    def __init__(self, config, s3):
        list.__init__(self)
        paginator=s3.get_paginator("list_objects_v2")
        pages=paginator.paginate(Bucket=config["globals"]["bucket"],
                                 Prefix="%s/lambdas" % config["globals"]["app"])
        for struct in pages:
            if "Contents" in struct:
                self+=[Lambda.create_s3(obj["Key"])
                       for obj in struct["Contents"]]

    @property
    def grouped(self):
        keys={}
        for commit in self:
            keys.setdefault(commit["name"], {})
            keys[commit["name"]][commit["hexsha"]]=commit
        return keys
                
    @property
    def latest(self):
        keys={}
        for commit in sorted(self,
                             key=lambda x: x["timestamp"]):
            keys[commit["name"]]=commit
        return keys

if __name__=="__main__":
    pass
