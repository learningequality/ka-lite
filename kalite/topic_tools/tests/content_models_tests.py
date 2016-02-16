from peewee import Using

from kalite.testing.base import KALiteTestCase
from kalite.topic_tools.content_models import update_item, get_random_content, get_content_item, get_content_items, \
    Item, get_topic_nodes, set_database, get_content_parents


class ContentModelRegressionTestCase(KALiteTestCase):

    @set_database
    def setUp(self, db=None):
        self.db = db
        with Using(db, [Item], with_transaction=False):
            parent = self.parent = Item.create(
                title="Foo",
                description="Bar",
                available=True,
                kind="Topic",
                id="1",
                slug="foo",
                path="foopath"
            )
            self.available_item = Item.create(
                title="available_item",
                description="Bingo",
                available=True,
                kind="Topic",
                id="2",
                slug="avail",
                path="avail",
                parent=parent
            )
            self.unavailable_item = Item.create(
                title="Unavailable item",
                description="baz",
                available=False,
                kind="Topic",
                id="3",
                slug="unavail",
                path="unavail",
                parent=parent
            )

    def tearDown(self):
        with Using(self.db, [Item], with_transaction=False):
            self.available_item.delete_instance()
            self.unavailable_item.delete_instance()
            self.parent.delete_instance()

    def test_get_topic_nodes(self):
        """ Test for issue #3997 -- only "available" items should be sent to the sidebar """
        children = get_topic_nodes(parent="1")
        self.assertEqual(children, [{
            'available': True,
            'description': self.available_item.description,
            'id': self.available_item.id,
            'kind': self.available_item.kind,
            'path': self.available_item.path,
            'slug': self.available_item.slug,
            'title': self.available_item.title,
        }])


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


class ContentModelsTestCase(KALiteTestCase):

    def test_get_content_parents(self):
        """
        The function get_content_parents() should return a empty list when an empty list of ids is passed to it.
        """
        self.assertEqual(get_content_parents(ids=list()), list())
