"""
Testing of the main-used internet utility functions
"""

from django.test import LiveServerTestCase

from fle_utils.internet.functions import am_i_online


class OnlineTests(LiveServerTestCase):
    def test_am_online(self):
        """The only thing I'm guaranteed to have online?  Myself."""

        #
        self.assertTrue(am_i_online(self.live_server_url, timeout=10), "Basic GET on myself")
        self.assertFalse(am_i_online("http://this.server.should.never.exist.or.else.we.are.screwed/", timeout=10), "Basic failure to GET")

        # expected_val
        self.assertFalse(am_i_online(self.live_server_url, expected_val="foo", timeout=10), "Test expected_val string fails")

        # search_string
        self.assertTrue(am_i_online(self.live_server_url, search_string="KA Lite", timeout=10), "Test search_string should succeed")
        self.assertFalse(am_i_online(self.live_server_url, search_string="foofoofoo", timeout=10), "Test search_string fails")


