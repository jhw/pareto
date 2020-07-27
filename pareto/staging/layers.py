import re

def layer_project_name(config, pkg):
    return "%s-%s-layer" % (config["globals"]["app"],
                            pkg["name"])

class LayerPackage(dict):

    CLIDelimiter="="

    LatestZip="LATEST.zip"

    @classmethod
    def create(self, config, name, version=None):
        pkg=LayerPackage()
        pkg["app"]=config["globals"]["app"]
        pkg["name"]=name
        if version:
            pkg["version"]=version
            pkg["pip_source"]="%s==%s" % (name, version)
            pkg["artifacts_name"]="%s.zip" % version.replace(".", "-")
        else:
            pkg["version"]=None
            pkg["pip_source"]=name
            pkg["artifacts_name"]=self.LatestZip
        return pkg
    
    def validate_cli(fn):
        def wrapped(self, config, pkgstr):
            if "-" in pkgstr:
                raise RuntimeError("please use = as version delimiter")
            if (self.CLIDelimiter in pkgstr and
                not re.search("(\\d+\\.)*\\d+$", pkgstr)):
                raise RuntimeError("package definition has invalid format")
            return fn(self, config, pkgstr)
        return wrapped
    
    @classmethod
    @validate_cli
    def create_cli(self, config, pkgstr):
        tokens=pkgstr.split(self.CLIDelimiter)
        pkg=LayerPackage()
        pkg["app"]=config["globals"]["app"]
        pkg["name"]=tokens[0]
        if len(tokens) > 1:
            pkg["version"]=tokens[1]
            pkg["pip_source"]="%s==%s" % tuple(tokens)
            pkg["artifacts_name"]="%s.zip" % tokens[1].replace(".", "-")
        else:
            pkg["version"]=None
            pkg["pip_source"]=pkg["name"]
            pkg["artifacts_name"]=self.LatestZip
        return pkg

    """
    - no need to include `pip_source` and `artifacts_name" when loading from s3 as not creating any new layers at this stage
    - but you need to include `app` if you want to render to s3
    """
    
    @classmethod
    def create_s3(self, s3key):
        tokens=s3key.split("/")
        pkg=LayerPackage()
        pkg["app"]=tokens[0]
        pkg["name"]=tokens[-2]
        if tokens[-1]==self.LatestZip:
            pkg["version"]=None
        else:
            pkg["version"]=tokens[-1].split(".")[0].replace("-", ".")
        return pkg
        
    def __init_(self, kwargs={}):
        dict.__init__(self, kwargs)

    def __str__(self):
        filename="%s.zip" % self["version"].replace(".", "-") if ("version" in self and self["version"]) else self.LatestZip
        return "%s/layers/%s/%s" % (self["app"],
                                    self["name"],
                                    filename)

class LayerPackages(list):

    def __init__(self, config, s3):
        list.__init__(self)
        paginator=s3.get_paginator("list_objects_v2")
        pages=paginator.paginate(Bucket=config["globals"]["bucket"],
                                 Prefix="%s/layers" % config["globals"]["app"])
        for struct in pages:
            if "Contents" in struct:
                self+=[LayerPackage.create_s3(obj["Key"])
                       for obj in struct["Contents"]]

    def exists(self, package):
        for pkg in self:
            if str(pkg)==str(package):
                return True
        return False
                
if __name__=="__main__":
    pass

