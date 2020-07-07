import json, unittest

class IndexTest(unittest.TestCase):

    def test_handler(self):
        from hello_post_api.index import handler
        resp=handler({"hello": "world"}, None)
        self.assertTrue("statusCode" in resp)
        self.assertEqual(resp["statusCode"], 200)
        self.assertTrue("body" in resp)
        body=json.loads(resp["body"])
        self.assertTrue("hello" in body)

if __name__=="__main__":
    unittest.main()
