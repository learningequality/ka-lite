import json

from kalite.testing.base import KALiteClientTestCase
from kalite.testing.mixins.facility_mixins import FacilityMixins

class TestCoachRedirect(FacilityMixins, KALiteClientTestCase):
    """
    Regression test for https://github.com/learningequality/ka-lite/issues/3857
    Ensures that the login api response for a coach redirects to the proper page.
    """

    def setUp(self):
        super(TestCoachRedirect, self).setUp()
        self.password = "abc123"
        self.coach = self.create_teacher(password=self.password)

    def test(self):
        resp = self.client.post(
            self.reverse("api_dispatch_list", kwargs={"resource_name": "user"}) + "login/",
            json.dumps({
                "username": self.coach.username,
                "password": self.password,
                "facility": self.coach.facility.id,
            }),
            content_type="application/json",
        )
        redirect = json.loads(resp.content).get("redirect")
        self.assertEqual(redirect, self.reverse("coach_reports"), "Logging in as coach does not redirect!")
