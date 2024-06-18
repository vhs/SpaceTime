# To run these unit tests from command line:
#
# python -m unittest test_vhsapi
#
import unittest
from vhsapi import VHSApi


class TestVHSApi(unittest.TestCase):

    # ----Query----

    def test_query_success(self):
        v = VHSApi()
        r = v.query("door")
        self.assertTrue(r == "open" or r == "closed")

    def test_query_timeout(self):
        v = VHSApi(timeout=0)
        self.assertFalse(v.query("door"))

    def test_query_connection_error(self):
        v = VHSApi(api_url="http://doesnotexist.vanhack.ca/")
        self.assertFalse(v.query("door"))

    def test_query_no_json(self):
        v = VHSApi(api_url="http://www.google.ca/?q=")
        self.assertFalse(v.query("door"))

    def test_query_bad_url(self):
        v = VHSApi(api_url="https://api.vanhack.ca/")
        self.assertFalse(v.query("door"))

    # ----Update----

    def test_update_success(self):
        v = VHSApi()
        self.assertTrue("v1" == v.update("test1", "v1") == v.query("test1"))
        self.assertTrue("v2" == v.update("test1", "v2") == v.query("test1"))

    def test_update_timeout(self):
        v = VHSApi(timeout=0)
        self.assertFalse(v.update("test1", "v1"))

    def test_update_connection_error(self):
        v = VHSApi(api_url="http://doesnotexist.vanhack.ca/")
        self.assertFalse(v.update("test1", "v1"))

    def test_update_no_json(self):
        v = VHSApi(api_url="http://www.google.ca/?q=")
        self.assertFalse(v.update("test1", "v1"))

    def test_update_bad_url(self):
        v = VHSApi(api_url="https://api.vanhack.ca/")
        self.assertFalse(v.update("test1", "v1"))


if __name__ == "_main_":
    unittest.main()
