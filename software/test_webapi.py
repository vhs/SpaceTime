# To run these unit tests from command line:
#
# python -m unittest test_webapi
#

import unittest
from unittest import mock
from os import environ as env

import requests
from exceptions import TestLiveOverrideException
from webapi import WebApi

#
# Note that the Update tests actually change the live status. It leaves the status as offline.
#

if env.get("USE_LIVE") != "YESIAMSURE":
    raise TestLiveOverrideException(
        "This test runs on live. Run with USE_LIVE=YESIAMSURE to run test"
    )


class TestWebApi(unittest.TestCase):

    # ----Query----

    def test_query_success(self):
        v = WebApi()

        r = v.query("status")

        self.assertTrue(r == "open" or r == "closed")

    def test_query_timeout(self):
        v = WebApi(api_url="https://1.2.3.4/api/status/", timeout=0)

        self.assertFalse(v.query("status"))

    def test_query_connection_error(self):
        # If querying a different server, we shouldn't be using our actual API key!
        v = WebApi(api_url="http://doesnotexist.isvhsopen.com/", api_key="BADBADBAD")

        self.assertFalse(v.query("status"))

    def test_query_no_json(self):
        # If querying a different server, we shouldn't be using our actual API key!
        v = WebApi(api_url="https://api.vanhack.ca/s/vhs/data/door.txt")
        self.assertFalse(v.query("status"))

    def test_query_bad_url(self):
        v = WebApi(api_url="https://isvhsopen.com/")
        self.assertFalse(v.query("status"))

    # ----Update----

    def test_update_success(self):
        # Note that this only checks the response json to ensure it matches
        # the update; we don't wait and then query to verify, but just trust it.
        v = WebApi()

        j = v.update("open", "12:34")

        self.assertTrue(
            j["status"] == "open"
            and (
                j["openUntil"].find("12:34:00") == 11
                or j["openUntil"].find("12:34:00") == 12
            )
        )

        j = v.update("closed")

        self.assertTrue(j["status"] == "closed" and j.get("openUntil") == None)

    def test_bad_key(self):
        v = WebApi(api_key="BADBADBAD")
        self.assertFalse(v.update("open", "12:34"))

    def test_update_timeout(self):
        v = WebApi(timeout=0)
        self.assertFalse(v.update("open", "12:34"))

    def test_update_connection_error(self):
        # If querying a different server, we shouldn't be using our actual API key!
        v = WebApi(api_url="http://doesnotexist.isvhsopen.com/", api_key="BADBADBAD")
        self.assertFalse(v.update("open", "12:34"))

    def test_update_no_json(self):
        # If querying a different server, we shouldn't be using our actual API key!
        v = WebApi(api_url="http://www.google.ca/?q=", api_key="BADBADBAD")
        self.assertFalse(v.update("test1", "v1"))

    def test_update_bad_url(self):
        v = WebApi(api_url="https://isvhsopen.com/")
        self.assertFalse(v.update("test1", "v1"))


if __name__ == "_main_":
    unittest.main()
