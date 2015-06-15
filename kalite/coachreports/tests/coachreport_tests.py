import json

from django.conf import settings
logging = settings.LOG

from kalite.testing.base import KALiteTestCase
from kalite.testing.mixins.django_mixins import CreateAdminMixin
from kalite.testing.mixins.securesync_mixins import CreateZoneMixin
from kalite.testing.mixins.facility_mixins import FacilityMixins
from kalite.testing.mixins.student_progress_mixins import StudentProgressMixin


class ExternalAPITests(FacilityMixins,
                       StudentProgressMixin,
                       CreateZoneMixin,
                       CreateAdminMixin,
                       KALiteTestCase):
    """
    These tests test the API endpoints that are external to the coachreports app, but on which it depends
    for functionality.
    """

    def setUp(self):
        super(ExternalAPITests, self).setUp()

        self.admin_data = {"username": "admin", "password": "admin"}
        self.admin = self.create_admin(**self.admin_data)
        self.facility = self.create_facility()

        self.api_facility_url = self.reverse("api_dispatch_list", kwargs={"resource_name": "facility"})
        self.api_group_url = self.reverse("api_dispatch_list", kwargs={"resource_name": "group"})
        self.zone = self.create_zone()
        self.device_zone = self.create_device_zone(self.zone)
        self.facility = self.create_facility()

        self.group = self.create_group(name='group1', facility=self.facility)
        self.empty_group = self.create_group(name='empty_group', facility=self.facility)

    def test_facility_endpoint(self):
        self.client.login(username='admin', password='admin')
        facility_resp = json.loads(self.client.get("%s?zone_id=%s" % (self.api_facility_url, self.zone.id)).content)
        objects = facility_resp.get("objects")
        self.assertEqual(len(objects), 1, "API response incorrect")
        self.assertEqual(objects[0]["name"], "facility1", "API response incorrect")
        self.client.logout()

    def test_group_endpoint(self):
        self.client.login(username='admin', password='admin')
        group_resp = json.loads(self.client.get("%s?facility_id=%s" % (self.api_group_url, self.facility.id)).content)
        objects = group_resp.get("objects")
        self.assertEqual(len(objects), 2, "API response incorrect")
        self.assertEqual(objects[0]["name"], "group1", "API response incorrect")
        self.assertEqual(objects[1]["name"], "empty_group", "API response incorrect")
        self.client.logout()

class InternalAPITests(FacilityMixins,
                       StudentProgressMixin,
                       CreateZoneMixin,
                       CreateAdminMixin,
                       KALiteTestCase):
    """
    These tests test the API endpoints that are internal to the coachreports app.
    """

    def setUp(self):
        super(InternalAPITests, self).setUp()

        self.admin_data = {"username": "admin", "password": "admin"}
        self.admin = self.create_admin(**self.admin_data)

        self.zone = self.create_zone()
        self.device_zone = self.create_device_zone(self.zone)
        self.facility = self.create_facility()

        self.group = self.create_group(name='group1', facility=self.facility)
        self.empty_group = self.create_group(name='empty_group', facility=self.facility)

    def test_learner_log_endpoint(self):
        response_keys = ["logs","contents","learners","page","pages","limit"]
        self.client.login(username='admin', password='admin')
        api_resp = json.loads(self.client.get("%s?facility_id=%s" % (self.reverse("learner_logs"), self.facility.id)).content)
        for key in response_keys:
            assert key in api_resp, "{key} not found in learner log API response".format(key)
        self.client.logout()

    def test_aggregate_endpoint(self):
        response_keys = ["content_time_spent","exercise_attempts","exercise_mastery", "total_time_logged", "learner_events"]
        self.client.login(username='admin', password='admin')
        api_resp = json.loads(self.client.get("%s?facility_id=%s" % (self.reverse("aggregate_learner_logs"), self.facility.id)).content)
        for key in response_keys:
            assert key in api_resp, "{key} not found in learner log API response".format(key)
        self.client.logout()

    def test_aggregate_endpoint_different_logs(self):
        # Regression test for #3799

        self.student = self.create_student()
        self.create_video_log(user=self.student)
        self.create_exercise_log(user=self.student)

        response_keys = ["content_time_spent","exercise_attempts","exercise_mastery", "total_time_logged", "learner_events"]
        self.client.login(username='admin', password='admin')
        api_resp = json.loads(self.client.get("%s?facility_id=%s" % (self.reverse("aggregate_learner_logs"), self.facility.id)).content)
        for key in response_keys:
            assert key in api_resp, "{key} not found in learner log API response".format(key)
        self.client.logout()
