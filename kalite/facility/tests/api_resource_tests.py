from kalite.testing.base import KALiteClientTestCase
from kalite.testing.mixins.facility_mixins import FacilityMixins

class TestCoachRedirect(FacilityMixins, KALiteClientTestCase):

    def setUp(self):
        super(TestCoachRedirect, self).setUp()
        self.password = "abc123"
        self.coach = self.create_teacher(password=self.password)

    def test(self):
        resp = self.client.post(
            self.reverse("api_dispatch_list", kwargs={"resource_name": "facility"}) + "login",
            data={
                "username": self.coach.username,
                "password": self.password,
                "facility": self.coach.facility,
            },
            content_type="application/json"
        )
        redirect = resp.get("redirect", None)
        self.assertEqual(redirect, self.reverse("zone_redirect"), "Logging in as coach does not redirect!")
