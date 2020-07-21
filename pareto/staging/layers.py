import re, unittest

def layer_project_name(config, pkg):
    return "%s-%s-layer" % (config["globals"]["app"],
                            pkg["name"])

class LayerPackage(dict):

    CLIDelimiter="="

    LatestZip="LATEST.zip"
    
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
        
class LayerPackageTest(unittest.TestCase):

    Config={"globals": {"app": "foobar"}}
    
    def test_create_cli_latest(self):        
        pkg=LayerPackage.create_cli(self.Config,
                                    "pymorphy2")
        self.assertEqual(pkg["name"], "pymorphy2")
        self.assertEqual(pkg["version"], None)
        self.assertEqual(pkg["pip_source"], "pymorphy2")
        self.assertEqual(pkg["artifacts_name"], "LATEST.zip")

    def test_create_cli_versioned(self):        
        pkg=LayerPackage.create_cli(self.Config,
                                    "pymorphy2=0.8")
        self.assertEqual(pkg["name"], "pymorphy2")
        self.assertEqual(pkg["version"], "0.8")
        self.assertEqual(pkg["pip_source"], "pymorphy2==0.8")
        self.assertEqual(pkg["artifacts_name"], "0-8.zip")

    def test_create_s3_latest(self):        
        pkg=LayerPackage.create_s3("foobar/layers/pymorphy2/LATEST.zip")
        self.assertEqual(pkg["app"], "foobar")
        self.assertEqual(pkg["name"], "pymorphy2")
        self.assertEqual(pkg["version"], None)

    def test_create_s3_versioned(self):        
        pkg=LayerPackage.create_s3("foobar/layers/pymorphy2/0-8.zip")
        self.assertEqual(pkg["app"], "foobar")
        self.assertEqual(pkg["name"], "pymorphy2")
        self.assertEqual(pkg["version"], "0.8")

    def test_str_latest(self):
        pkg=LayerPackage(app="foobar",
                         name="pymorphy2")
        self.assertEqual("foobar/layers/pymorphy2/LATEST.zip", str(pkg))

    def test_str_versioned(self):
        pkg=LayerPackage(app="foobar",
                         name="pymorphy2",
                         version="0.8");
        self.assertEqual("foobar/layers/pymorphy2/0-8.zip", str(pkg))
            
if __name__=="__main__":
    unittest.main()

