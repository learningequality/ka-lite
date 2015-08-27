from kalite.testing.base import KALiteTestCase
from kalite.caching import initialize_content_caches


class UpdatesTestCase(KALiteTestCase):
    """
    Generic setup / teardown for updates tests
    """
    def setUp(self):
        super(UpdatesTestCase, self).setUp()

        # Set up the topic tree
        initialize_content_caches(force=True)

