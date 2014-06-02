from .. import stamp_availability_on_topic
from kalite.testing import KALiteTestCase
from kalite.topic_tools import get_topic_tree


class UpdatesTestCase(KALiteTestCase):
    """
    Generic setup / teardown for updates tests
    """
    def setUp(self):
        super(UpdatesTestCase, self).setUp()

        # Set up the topic tree
        stamp_availability_on_topic(get_topic_tree(), force=True, stamp_urls=True)

