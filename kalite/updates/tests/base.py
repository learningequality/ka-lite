from main.topic_tools import get_topic_tree
from testing import KALiteTestCase
from updates import stamp_availability_on_topic


class UpdatesTestCase(KALiteTestCase):
    """
    Generic setup / teardown for updates tests
    """
    def setUp(self):
        super(UpdatesTestCase, self).setUp()

        # Set up the topic tree
        stamp_availability_on_topic(get_topic_tree(), force=True, stamp_urls=True)

