from kalite.testing.base import KALiteTestCase
from kalite.topic_tools.content_models import update_item, get_random_content, get_content_item, get_content_items


class UpdateItemTestCase(KALiteTestCase):
    
    def test_update_item(self):
        item = get_random_content()[0]
        available = item.get("available")
        inverse_available = not available
        update_item({"available": inverse_available}, item.get("path"))
        item2 = get_content_item(content_id=item.get("id"))
        self.assertEqual(item2.get("available"), inverse_available)

    def test_update_item_with_duplicated_item(self):
        """
        Tests that update_items updates *all* items with the same id.
        Content item ids are not unique (though paths are) because the db is not normalized, so items with the same
          id should be updated together.
        """
        item_id = "addition_1"  # This item is known to be duplicated.
        items = get_content_items(ids=[item_id])
        self.assertGreater(len(items), 1)
        item = items[0]
        available = item.get("available")
        inverse_available = not available
        update_item({"available": inverse_available}, item.get("path"))
        items = get_content_items(ids=[item.get("id")])
        self.assertTrue(all([item.get("available") == inverse_available for item in items]))
