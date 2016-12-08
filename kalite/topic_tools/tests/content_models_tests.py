from kalite.testing.base import KALiteTestCase
from kalite.topic_tools.content_models import update_item, get_random_content, get_content_item, \
    get_topic_nodes, get_content_parents


class ContentModelRegressionTestCase(KALiteTestCase):

    def test_get_topic_nodes(self):
        """ Test for issue #3997 -- only "available" items should be sent to the sidebar """
        children = get_topic_nodes(parent=self.content_root)
        for child in children:
            self.assertTrue(child.available)


class UpdateItemTestCase(KALiteTestCase):
    
    def test_update_item(self):
        item = get_random_content()[0]
        available = item.get("available")
        inverse_available = not available
        update_item({"available": inverse_available}, item.get("path"))
        item2 = get_content_item(content_id=item.get("id"))
        self.assertEqual(item2.get("available"), inverse_available)


class ContentModelsTestCase(KALiteTestCase):

    def test_get_content_parents(self):
        """
        The function get_content_parents() should return a empty list when an
        empty list of ids is passed to it.
        """
        self.assertEqual(get_content_parents(ids=list()), list())
