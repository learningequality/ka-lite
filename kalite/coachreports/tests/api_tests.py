import json

from django.core.urlresolvers import reverse
from tastypie.exceptions import Unauthorized

from kalite.testing import KALiteClient, KALiteTestCase
from kalite.testing.mixins import CreateAdminMixin, CreatePlaylistProgressMixin, FacilityMixins


class TestGetTopicTree(KALiteTestCase):

    def test_get_root(self):
        """Get the root node of the topic tree"""

        resp = self.client.get(reverse("get_topic_tree_by_kinds", kwargs={"topic_path": "/"}))
        self.assertEqual(resp.status_code, 200, "Status code should be 200 (actual: %s)" % resp.status_code)

        topic_tree = json.loads(resp.content)
        self.assertEqual(topic_tree["title"], "Khan Academy", "Topic root should be Khan Academy (actual: %s)" % topic_tree["title"])

    def test_get_math(self):
        """Get the math node of the topic tree; url has no trailing slash"""

        resp = self.client.get(reverse("get_topic_tree_by_kinds", kwargs={"topic_path": "/math"}))
        self.assertEqual(resp.status_code, 200, "Status code should be 200 (actual: %s)" % resp.status_code)

        topic_tree = json.loads(resp.content)
        self.assertEqual(topic_tree["title"], "Math", "Topic root should be Khan Academy (actual: %s)" % topic_tree["title"])

    def test_get_math_trailing_slash(self):
        """Get the math node of the topic tree; url has trailing slash"""

        # Now do the same thing, but with a trailing slash
        resp = self.client.get(reverse("get_topic_tree_by_kinds", kwargs={"topic_path": "/math/"}))
        self.assertEqual(resp.status_code, 200, "Status code should be 200 (actual: %s)" % resp.status_code)

        topic_tree = json.loads(resp.content)
        self.assertEqual(topic_tree["title"], "Math", "Topic root should be Khan Academy (actual: %s)" % topic_tree["title"])

    def test_get_404(self):
        """Get a node of the topic tree that doesn't exist"""

        resp = self.client.get(reverse("get_topic_tree_by_kinds", kwargs={"topic_path": "/foo"}))
        self.assertEqual(resp.status_code, 404, "Status code should be 404 (actual: %s)" % resp.status_code)


class PlaylistProgressAPITest(CreatePlaylistProgressMixin,
                              CreateAdminMixin,
                              FacilityMixins,
                              KALiteTestCase):

    def setUp(self):
        # Create fake accounts and data
        super(PlaylistProgressAPITest, self).setUp()
        self.setup_fake_device()
        self.facility = self.create_facility()
        self.admin = self.create_admin()
        self.test_student = self.create_student()
        self.hacker_student = self.create_student(username="hacker", password="hacker")
        self.client = KALiteClient()

    def test_playlist_progress_resource(self, auth_test=False):
        self.playlist = self.create_playlist_progress(self.test_student)
        # Playlist Progress (high-level)
        if not auth_test:
            self.client.login(username=self.test_student.username, password="password", facility=self.facility.id)
        resp = self.client.get("%s?user_id=%s" % (reverse("api_dispatch_list", kwargs={"resource_name": "playlist_progress"}), self.test_student.id))
        json_resp = json.loads(resp.content)

        # Get our playlist
        pl_response = next((entry for entry in json_resp["objects"] if entry["id"] == self.playlist.id), None)
        self.assertTrue(pl_response, "No playlist response found")

        # Sample to check that we are getting what we expect
        self.assertEqual(pl_response["ex_pct_struggling"], 50, "Incorrect value returned by API")
        self.assertEqual(pl_response["vid_pct_complete"], 20, "Incorrect value returned by API")
        self.assertEqual(pl_response["quiz_status"], "borderline", "Incorrect value returned by API")

        self.client.logout()

    def test_playlist_progress_detail_resource(self, auth_test=False):
        self.playlist = self.create_playlist_progress(self.test_student)
        # Playlist Progress Details
        if not auth_test:
            self.client.login(username=self.test_student.username, password="password", facility=self.facility.id)
        resp = self.client.get("%s?user_id=%s&playlist_id=%s" % (reverse("api_dispatch_list", kwargs={"resource_name": "playlist_progress_detail"}), self.test_student.id, self.playlist.id))
        pl_response = json.loads(resp.content)["objects"]

        # Sample to check that we are getting what we expect
        self.assertEqual(len(pl_response), 8, "Incorrect value returned by API")
        self.assertEqual(pl_response[0]["status"], "complete", "Incorrect value returned by API")
        self.assertEqual(pl_response[0]["score"], 100, "Incorrect value returned by API")
        self.assertEqual(pl_response[1]["status"], "struggling", "Incorrect value returned by API")
        self.assertEqual(pl_response[1]["score"], 50, "Incorrect value returned by API")

        self.client.logout()

    def test_playlist_progress_detail_resource_no_quiz(self, auth_test=False):
        # Regression test for error during missing entry PlayListProgressDetail function call.
        self.playlist = self.create_playlist_progress(self.test_student, quiz=False)
        # Playlist Progress Details
        if not auth_test:
            self.client.login(username=self.test_student.username, password="password", facility=self.facility.id)
        resp = self.client.get("%s?user_id=%s&playlist_id=%s" % (reverse("api_dispatch_list", kwargs={"resource_name": "playlist_progress_detail"}), self.test_student.id, self.playlist.id))
        pl_response = json.loads(resp.content)["objects"]

        # Sample to check that we are getting what we expect
        self.assertEqual(len(pl_response), 8, "Incorrect value returned by API")
        self.assertEqual(pl_response[0]["status"], "complete", "Incorrect value returned by API")
        self.assertEqual(pl_response[0]["score"], 100, "Incorrect value returned by API")
        self.assertEqual(pl_response[1]["status"], "struggling", "Incorrect value returned by API")
        self.assertEqual(pl_response[1]["score"], 50, "Incorrect value returned by API")

        self.client.logout()

    def test_playlist_progress_resource_auth(self):
        # Admins should be able to view
        self.client.login(username=self.admin.username, password="admin")
        self.test_playlist_progress_resource(auth_test=True)
        self.client.logout()

        # other students should not
        self.client.login(username=self.hacker_student.username, password="hacker", facility=self.facility.id)
        with self.assertRaises(Unauthorized):
            self.test_playlist_progress_resource(auth_test=True)
        self.client.logout()

        # nor should not logged in users
        with self.assertRaises(Unauthorized):
            self.test_playlist_progress_resource(auth_test=True)
        self.client.logout()

    def test_playlist_progress_detail_resource_auth(self):
        # Admins should be able to view
        self.client.login(username=self.admin.username, password="admin")
        self.test_playlist_progress_detail_resource(auth_test=True)
        self.client.logout()

        # other students should not
        self.client.login(username=self.hacker_student.username, password="hacker", facility=self.facility.id)
        with self.assertRaises(Unauthorized):
            self.test_playlist_progress_detail_resource(auth_test=True)
        self.client.logout()

        # nor should not logged in users
        with self.assertRaises(Unauthorized):
            self.test_playlist_progress_detail_resource(auth_test=True)
        self.client.logout()
