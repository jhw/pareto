import unittest

class IndexTest(unittest.TestCase):

    def test_handler(self):
        from hello_action_3.index import handler
        resp=handler({}, None)
        self.assertTrue("hello" in resp)

if __name__=="__main__":
    unittest.main()
