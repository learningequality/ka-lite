import logging
import requests

from django.test.utils import override_settings

from fle_utils.internet.functions import am_i_online

from securesync.models import Device

from kalite.testing.base import KALiteClientTestCase
from kalite.testing.mixins.django_mixins import CreateAdminMixin
from requests.exceptions import ConnectionError


logger = logging.getLogger(__name__)


class RegistrationRedirectTestCase(CreateAdminMixin, KALiteClientTestCase):
    """
    Tests that the when the user is unregistered and "offline", they are not redirected to the registration page.
    "Offline" in this case just means the central server is unreachable.
    See #4282: https://github.com/learningequality/ka-lite/issues/4282
    """

    def setUp(self):
        super(RegistrationRedirectTestCase, self).setUp()
        admin_data = {"username": "admin", "password": "admin"}
        self.create_admin(**admin_data)
        self.client.login(**admin_data)
    
    def test_online(self):
        try:
            response = requests.get("http://google.com",)
            google_is_online = response.status_code in (200, 301)
        except ConnectionError:
            logger.warning("Running test_online while offline")
            google_is_online = False
        
        self.assertEqual(am_i_online(), google_is_online)

    @override_settings(CENTRAL_SERVER_URL="http://127.0.0.1:8997")  # We hope this is unreachable
    def test_not_redirected_when_offline(self):
        self.assertFalse(Device.get_own_device().is_registered(), "The device should be unregistered!")
        
        register_device_url = self.reverse("register_public_key")
        response = self.client.get(register_device_url, follow=False)
        self.assertEqual(response.status_code, 200)
        
        self.assertFalse(am_i_online(), "Central server should be unreachable!")
        updated_videos_url = self.reverse("update_videos")
        response = self.client.get(updated_videos_url, follow=True)
        redirect_chain = response.redirect_chain  # Will be the empty list if there are no redirects
        self.assertFalse(redirect_chain, "Should not be redirected when the central server is not reachable! "
                                         "Redirect chain: {0}".format(redirect_chain))
