import unittest

class IndexTest(unittest.TestCase):

    def test_hello(self):
        from hello_function.index import handler
        resp=handler({}, None)
        self.assertTrue("statusCode" in resp)
        self.assertEqual(resp["statusCode"], 200)

if __name__=="__main__":
    unittest.main()
