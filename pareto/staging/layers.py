import re, unittest

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
            package["version"]=tokens[1]
            package["pip_source"]="%s==%s" % tuple(tokens)
            package["artifacts_name"]="%s.zip" % tokens[1].replace(".", "-")
        else:
            package["version"]=None
            package["pip_source"]=package["name"]
            package["artifacts_name"]="LATEST.zip"
        return package

    def __init_(self, kwargs={}):
        dict.__init__(self, kwargs)

class LayerPackageTest(unittest.TestCase):

    def test_latest(self):        
        key=LayerPackage.parse("pymorphy2")
        self.assertEqual(key["name"], "pymorphy2")
        self.assertEqual(key["version"], None)
        self.assertEqual(key["pip_source"], "pymorphy2")
        self.assertEqual(key["artifacts_name"], "LATEST.zip")

    def test_version(self):        
        key=LayerPackage.parse("pymorphy2=0.8")
        self.assertEqual(key["name"], "pymorphy2")
        self.assertEqual(key["version"], "0.8")
        self.assertEqual(key["pip_source"], "pymorphy2==0.8")
        self.assertEqual(key["artifacts_name"], "0-8.zip")
            
if __name__=="__main__":
    unittest.main()

