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
        """
        - if version doesn't exist then don't set it
        - build_layer.py assumes missing version == LATEST
        """
        if len(tokens) > 1:
            package["version"]={"raw": tokens[1],
                                "formatted": tokens[1].replace(".", "-")}
        return package

    def __init_(self, kwargs={}):
        dict.__init__(self, kwargs)
    
if __name__=="__main__":
    for packagestr in ["pymorphy2",
                       "pymorphy2=0.8"]:
        print (LayerPackage.parse(packagestr))


