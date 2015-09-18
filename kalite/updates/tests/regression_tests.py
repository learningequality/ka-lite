from django.conf import settings
from django.test.utils import override_settings

from fle_utils.internet.functions import am_i_online

from securesync.models import Device

from kalite.testing.base import KALiteClientTestCase
from kalite.testing.mixins.django_mixins import CreateAdminMixin

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

    @override_settings(CENTRAL_SERVER_URL="http://127.0.0.1:8997")  # We hope this is unreachable
    def test_not_redirected_when_offline(self):
        self.assertFalse(Device.get_own_device().is_registered(), "The device should be unregistered!")
        self.assertFalse(am_i_online(url=settings.CENTRAL_SERVER_URL), "Central server should be unreachable!")
        updated_videos_url = self.reverse("update_videos")
        response = self.client.get(updated_videos_url, follow=True)
        redirect_chain = response.redirect_chain  # Will be the empty list if there are no redirects
        self.assertFalse(redirect_chain, "Should not be redirected when the central server is not reachable! "
                                         "Redirect chain: {0}".format(redirect_chain))
