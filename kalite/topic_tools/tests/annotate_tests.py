
from kalite.topic_tools.annotate import update_content_availability
from kalite.testing.base import KALiteTestCase
from django.test import TestCase
from kalite.topic_tools.content_models import Item, annotate_content_models, set_database, unparse_model_data
from . import settings
from peewee import Using
from playhouse.shortcuts import model_to_dict
import json
import os

from django.test.utils import override_settings

from kalite.contentload import settings as contentload_settings

class AnnotateTestCase(TestCase):
    TITLE = "testing "
    AVAILABLE = False
    KIND = "Exercise"

    @set_database
    def setUp(self, db=None):
        self.db = db
        with Using(db, [Item], with_transaction=False):
            self.item = Item(
                title=self.TITLE,
                available=self.AVAILABLE,
                kind=self.KIND,
                description="test",
                id="counting-out-1-20-objects",
                slug="test",
                path="thepath",
                extra_fields={},
            )
            self.item.save()
        self.version_path = contentload_settings.KHAN_ASSESSMENT_ITEM_VERSION_PATH

        self.cleanup = False

        if not os.path.exists(self.version_path):

            with open(self.version_path, 'w') as f:
                f.write("stuff")
            self.cleanup = True

    def tearDown(self):
        with Using(self.db, [Item], with_transaction=False):
            self.item.delete_instance()

        if self.cleanup:
            try:
                os.remove(self.version_path)
            except OSError:
                pass

    def test_update_content_availability_true(self):

        with Using(self.db, [Item]):
            actual = dict(update_content_availability([unparse_model_data(model_to_dict(self.item))])).get("thepath")
            assert actual.get("available")

    def test_update_content_availability_false(self):

        try:
            os.rename(self.version_path, self.version_path + ".bak")
        except OSError:
            pass

        with Using(self.db, [Item]):
            actual = dict(update_content_availability([unparse_model_data(model_to_dict(self.item))])).get("thepath")
            # Update is only generated if changed from False to True, not from False to False, so should return None.
            assert not actual

        try:
            os.rename(self.version_path + ".bak", self.version_path)
        except OSError:
            pass
