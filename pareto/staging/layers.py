import re

def layer_project_name(config, package):
    return "%s-%s-layer" % (config["globals"]["app"],
                            package["name"])

class LayerPackage(dict):

    VersionDelimiter="="
    
    def validate(fn):
        def wrapped(self, packagestr):
            if "-" in packagestr:
                raise RuntimeError("please use = as version delimiter")
            if (self.VersionDelimiter in packagestr and
                not re.search("(\\d+\\.)*\\d+$", packagestr)):
                raise RuntimeError("package definition has invalid format")
            return fn(self, packagestr)
        return wrapped
    
    @classmethod
    @validate
    def parse(self, packagestr):
        package=LayerPackage()
        tokens=packagestr.split(self.VersionDelimiter)
        package["name"]=tokens[0]
        if len(tokens) > 1:
            package["pip_source"]="%s==%s" % tuple(tokens)
            package["artifacts_name"]="%s.zip" % tokens[1].replace(".", "-")
        else:
            package["pip_source"]=package["name"]
            package["artifacts_name"]="LATEST.zip"
        return package

    def __init_(self, kwargs={}):
        dict.__init__(self, kwargs)
    
if __name__=="__main__":
    for packagestr in ["pymorphy2",
                       "pymorphy2=0.8"]:
        print (LayerPackage.parse(packagestr))


