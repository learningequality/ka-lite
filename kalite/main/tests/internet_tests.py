"""
Testing of the main-used internet utility functions
"""

from django.test import LiveServerTestCase

from fle_utils.internet.functions import am_i_online


class OnlineTests(LiveServerTestCase):
    def test_am_online(self):
        """The only thing I'm guaranteed to have online?  Myself."""

        #
        self.assertTrue(am_i_online(self.live_server_url), "Basic GET on myself")
        self.assertFalse(am_i_online("http://this.server.should.never.exist.or.else.we.are.screwed/"), "Basic failure to GET")

        # expected_val
        self.assertFalse(am_i_online(self.live_server_url, expected_val="foo"), "Test expected_val string fails")

        # search_string
        self.assertTrue(am_i_online(self.live_server_url, search_string="KA Lite"), "Test search_string should succeed")
        self.assertFalse(am_i_online(self.live_server_url, search_string="foofoofoo"), "Test search_string fails")


