import unittest

class IndexTest(unittest.TestCase):

    def test_handler(self):
        from demo.hello_table_fn.index import handler
        resp=handler({"hello": "world"}, None)
        self.assertTrue("hello" in resp)

if __name__=="__main__":
    unittest.main()
