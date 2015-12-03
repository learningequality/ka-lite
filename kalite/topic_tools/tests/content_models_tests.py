from kalite.testing.base import KALiteTestCase
from kalite.topic_tools.content_models import update_item, get_random_content, get_content_item


class UpdateItemTestCase(KALiteTestCase):
    
    def test_update_item(self):
        item = get_random_content()[0]
        available = item.get("available")
        inverse_available = not available
        update_item({"available": inverse_available}, item.get("path"))
        item2 = get_content_item(content_id=item.get("id"))
        self.assertEqual(item2.get("available"), inverse_available)
