import boto3, re, unittest

from moto import mock_s3


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

@mock_s3
class LayerPackagesTest(unittest.TestCase):

    Config={"globals": {"app": "my-app",
                        "bucket": "foobar"}}

    Keys=["my-app/layers/lxml/LATEST.zip",
          "my-app/layers/pymorphy2/LATEST.zip",
          "my-app/layers/pymorphy2/0-8.zip"]
    
    def setUp(self):
        self.s3=boto3.client("s3")
        bucketname=self.Config["globals"]["bucket"]
        self.s3.create_bucket(Bucket=bucketname,
                              CreateBucketConfiguration={'LocationConstraint': 'EU'})
        for key in self.Keys:
            self.s3.put_object(Bucket=bucketname,
                               Key=key,
                               Body="{}")
        
    def test_hello(self):
        bucketname=self.Config["globals"]["bucket"]
        packages=LayerPackages(self.Config, self.s3)
        self.assertEqual(len(packages), len(self.Keys))
        
    def tearDown(self):
        bucketname=self.Config["globals"]["bucket"]
        struct=self.s3.list_objects(Bucket=bucketname)
        if "Contents" in struct:
            for obj in struct["Contents"]:
                self.s3.delete_object(Bucket=self.Config["globals"]["bucket"],
                                      Key=obj["Key"])
        self.s3.delete_bucket(Bucket=bucketname)
        
if __name__=="__main__":
    unittest.main()

