from kalite.testing import KALiteTestCase
from kalite.topic_tools import get_topic_tree
from kalite.caching import initialize_content_caches


class UpdatesTestCase(KALiteTestCase):
    """
    Generic setup / teardown for updates tests
    """
    def setUp(self):
        super(UpdatesTestCase, self).setUp()

        # Set up the topic tree
        initialize_content_caches(force=True)

