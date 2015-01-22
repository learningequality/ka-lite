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
