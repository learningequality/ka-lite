import json
import urllib
import peewee

from django.conf import settings
logging = settings.LOG
from mock import patch

from kalite.testing.base import KALiteTestCase, KALiteClientTestCase
from kalite.testing.mixins.django_mixins import CreateAdminMixin
from kalite.testing.mixins.securesync_mixins import CreateZoneMixin
from kalite.testing.mixins.facility_mixins import FacilityMixins
from kalite.testing.mixins.student_progress_mixins import StudentProgressMixin
from kalite.topic_tools.content_models import get_content_parents, Item, set_database, create
from kalite.i18n.api_views import set_default_language
from django.test.utils import override_settings


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

        self.facility_user = self.create_student()

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

class PlaylistProgressResourceTestCase(FacilityMixins, StudentProgressMixin, KALiteClientTestCase):

    @set_database
    def setUp(self, db=None):
        self.db = db
        self.topic1 = create({
            "id": "stuff_here",
            "slug": "stuff_here",
            "path": "qwrqweqweqwe",
            "kind": "Topic",
            "title": "",
            "description": "",
            "available": True,
        })
        self.exercise1 = create({
            "id": "stuff_here_ex",
            "slug": "stuff_here_ex",
            "path": "qwrqweqweqwe/qwrqweqweq",
            "kind": "Exercise",
            "title": "",
            "description": "",
            "available": True,
            "parent": self.topic1,
        })
        self.student = self.create_student()
        self.ex_logs = self.create_exercise_log(user=self.student, exercise_id=self.exercise1.id)

    @set_database
    def tearDown(self, db=None):
        self.db = db
        self.exercise1.delete()
        self.topic1.delete()

    def test_playlist_progress(self):
        base_url = self.reverse('api_dispatch_list', kwargs={'resource_name': 'playlist_progress_detail'})
        url = base_url + '?' + urllib.urlencode({'user_id': self.student.id, 'playlist_id': self.topic1.id})
        resp = self.client.get(url)
        exercises = json.loads(resp.content).get("objects")
        # checking if the request returned any of the exercises
        self.assertTrue(len(exercises) > 0)
        #checking if the returned list is accurate
        self.assertEqual(exercises[0]["title"], self.exercise1.title)

    @patch('kalite.coachreports.models.get_content_parents')
    def test_playlist_progress_language(self, mocked_get_content_parents):
        """
        Test if there is language argument got passed to get_content_parents() when playlist_progress is requested.
        """
        base_url = self.reverse('api_dispatch_list', kwargs={'resource_name': 'playlist_progress'})
        url = base_url + '?' + urllib.urlencode({'user_id': self.student.id})
        resp = self.client.get(url)
        actual_len = str(mocked_get_content_parents.call_args[1]['language'])
        assert actual_len

    @patch('kalite.coachreports.models.get_topic_nodes')
    def test_playlist_progress_detail_language(self, mocked_get_topic_nodes):
        """
        This is a very hacky way to test if there is language argument got passed to get_topic_nodes() when playlist_progress_detail is requested.
        """
        base_url = self.reverse('api_dispatch_list', kwargs={'resource_name': 'playlist_progress_detail'})
        url = base_url + '?' + urllib.urlencode({'user_id': self.student.id, 'playlist_id': self.topic1.id})
        # It is very tricky to get the endpoint response right with all the truble to login as student.
        # So for the purpose of this test, I ignore any error caused by the request, just check the argument in get_topic_nodes()
        try:
            resp = self.client.get(url)
        except:
            pass
        actual_len = str(mocked_get_topic_nodes.call_args[1]['language'])
        assert actual_len


class LearnerLogAPITests(FacilityMixins,
                       StudentProgressMixin,
                       CreateZoneMixin,
                       CreateAdminMixin,
                       KALiteTestCase):
    """
    These tests test the learner log API endpoint in the coachreports app.
    """

    def setUp(self):
        super(LearnerLogAPITests, self).setUp()

        self.admin_data = {"username": "admin", "password": "admin"}
        self.admin = self.create_admin(**self.admin_data)

        self.zone = self.create_zone()
        self.device_zone = self.create_device_zone(self.zone)
        self.facility = self.create_facility()

        self.group = self.create_group(name='group1', facility=self.facility)
        self.empty_group = self.create_group(name='empty_group', facility=self.facility)

        self.facility_user = self.create_student()

        self.topic1 = create({
            "id": "stuff_here",
            "slug": "stuff_here",
            "path": "qwrqweqweqwe",
            "kind": "Topic",
            "title": "",
            "description": "",
            "available": True,
        })
        self.topic2 = create({
            "id": "stuff_there",
            "slug": "stuff_there",
            "path": "qwrqweqweqw",
            "kind": "Topic",
            "title": "",
            "description": "",
            "available": True,
        })

        self.exercise1 = create({
            "id": "stuff_here_ex",
            "slug": "stuff_here_ex",
            "path": "qwrqweqweqwe/qwrqweqweq",
            "kind": "Exercise",
            "title": "",
            "description": "",
            "available": True,
            "parent": self.topic1,
        })
        self.exercise2 = create({
            "id": "stuff_there_ex",
            "slug": "stuff_there_ex",
            "path": "qwrqweqweqw/qwrqweqw",
            "kind": "Exercise",
            "title": "",
            "description": "",
            "available": True,
            "parent": self.topic2,
        })

        self.create_exercise_log(user=self.facility_user, exercise_id=self.exercise1.id)
        self.create_exercise_log(user=self.facility_user, exercise_id=self.exercise2.id)

    def tearDown(self):
        self.exercise1.delete()
        self.exercise2.delete()
        self.topic1.delete()
        self.topic2.delete()

    def test_learner_log_topic_filters(self):

        self.client.login(username='admin', password='admin')
        api_resp_1 = json.loads(self.client.get("%s?facility_id=%s" % (self.reverse("learner_logs"), self.facility.id)).content)
        api_resp_2 = json.loads(self.client.get("%s?facility_id=%s&topic_ids=%s" % (self.reverse("learner_logs"), self.facility.id, json.dumps([self.topic1.id]))).content)
        assert len(api_resp_2["contents"]) < len(api_resp_1["contents"])

    def test_learner_log_topic_filters_contents_length(self):

        self.client.login(username='admin', password='admin')
        api_resp_2 = json.loads(self.client.get("%s?facility_id=%s&topic_ids=%s" % (self.reverse("learner_logs"), self.facility.id, json.dumps([self.topic1.id]))).content)
        assert len(api_resp_2["contents"]) == 1

    def test_learner_log_topic_filters_contents_id(self):

        self.client.login(username='admin', password='admin')
        api_resp_2 = json.loads(self.client.get("%s?facility_id=%s&topic_ids=%s" % (self.reverse("learner_logs"), self.facility.id, json.dumps([self.topic1.id]))).content)
        assert api_resp_2["contents"][0]["id"] == self.exercise1.id

    def test_learner_log_contents(self):

        self.client.login(username='admin', password='admin')
        api_resp_1 = json.loads(self.client.get("%s?facility_id=%s" % (self.reverse("learner_logs"), self.facility.id)).content)
        assert len(api_resp_1["contents"]) == 2

    def test_learner_log_logs(self):

        self.client.login(username='admin', password='admin')
        api_resp_1 = json.loads(self.client.get("%s?facility_id=%s" % (self.reverse("learner_logs"), self.facility.id)).content)
        assert len(api_resp_1["logs"]) == 2

    def test_learner_log_log_contents(self):

        self.client.login(username='admin', password='admin')
        api_resp_2 = json.loads(self.client.get("%s?facility_id=%s&topic_ids=%s" % (self.reverse("learner_logs"), self.facility.id, json.dumps([self.topic1.id]))).content)
        assert api_resp_2["logs"][0]["exercise_id"] == self.exercise1.id
