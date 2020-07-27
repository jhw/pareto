from pareto.staging.layers import LayerPackage, LayerPackages

import boto3, unittest

from moto import mock_s3

class LayerPackageTest(unittest.TestCase):

    Config={"globals": {"app": "foobar"}}

    def test_create_latest(self):        
        pkg=LayerPackage.create(self.Config,
                                name="pymorphy2")
        self.assertEqual(pkg["name"], "pymorphy2")
        self.assertEqual(pkg["version"], None)
        self.assertEqual(pkg["pip_source"], "pymorphy2")
        self.assertEqual(pkg["artifacts_name"], "LATEST.zip")

    def test_create_versioned(self):        
        pkg=LayerPackage.create(self.Config,
                                name="pymorphy2",
                                version="0.8")
        self.assertEqual(pkg["name"], "pymorphy2")
        self.assertEqual(pkg["version"], "0.8")
        self.assertEqual(pkg["pip_source"], "pymorphy2==0.8")
        self.assertEqual(pkg["artifacts_name"], "0-8.zip")
    
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
        
    def test_exists(self):
        bucketname=self.Config["globals"]["bucket"]
        packages=LayerPackages(self.Config, self.s3)
        self.assertEqual(len(packages), len(self.Keys))
        for k, v in [("pymorphy2", True),
                     ("pymorphy2=0.8", True),
                     ("foobar", False)]:
            package=LayerPackage.create_cli(self.Config, k)
            self.assertEqual(packages.exists(package), v)
        
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

