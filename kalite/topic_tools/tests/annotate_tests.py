
from kalite.topic_tools.annotate import update_content_availability
from kalite.testing.base import KALiteTestCase
from django.test import TestCase
from kalite.topic_tools.content_models import Item, annotate_content_models, set_database, unparse_model_data
from . import settings 
from peewee import Using
from playhouse.shortcuts import model_to_dict
import json

class AnnotateTestCase(TestCase):
    TITLE = "testing "
    AVAILABLE = False
    KIND = "Exercise"
  
    thedict = {'uses_assessment_items': True}
    thestuff = [
    u'{"sha": "c2074685910760669c855d628b7a44ef8d828be9", "live": true, "id": "xde8147b8edb82294"}',
    u'{"sha": "76c7fd55c20dfe0f4f938745b73e1e7d0c4757ac", "live": true, "id": "xa5c8d62485b6bf16"}',
    u'{"sha": "a4318a5630a8766f55dc6830527dbaffc7fb917b", "live": true, "id": "x2313c50d4dfd4a0a"}',
    u'{"sha": "b350b21cf286a64c0e7869a6429fc6c5fd139c1f", "live": true, "id": "xcd7ba1c0c381fadb"}',
    u'{"sha": "e8ba59f1f99433fbd0360332f999cde76ab8976b", "live": true, "id": "x4cb56360820eece5"}',
    u'{"sha": "954fcd5885c36b841a22bc5bf89207bced27b8be", "live": true, "id": "xcc39b61282c884be"}',
    u'{"sha": "15070fc64826e1cd00665c38e2e42e5834ed359a", "live": true, "id": "x9c6c9733676e5240"}',
    u'{"sha": "89d992ba940c4ecaa7687d7a84ce632ead085882", "live": true, "id": "x8ae458b86dfe440b"}',
    u'{"sha": "54f92d19cabbd7647cd5d21d4678e8711431e9fb", "live": true, "id": "x8e7fd4a4b5b002c1"}',
    u'{"sha": "8d00285eae0fab5210dcfb325be7741e48c75681", "live": true, "id": "xeee62e178c0cfe6f"}',
    u'{"sha": "4453b349bad32a1e416e7e74af64e09e2c5810f8", "live": true, "id": "xdee0840c85c0add5"}',
    u'{"sha": "bb340ca13b104a9b9d1065b74a2fdfa423f817d1", "live": true, "id": "xa756d02df7435e1a"}',
    u'{"sha": "f65a9c4a6a8df260021fe424d562e8ff6d1741bd", "live": true, "id": "x6b9db70231ff254d"}',
    u'{"sha": "00808cbc066910be1220235faa7d93a9126f6a57", "live": true, "id": "x1855395b96b1e34f"}',
    u'{"sha": "90db973ee0fd319c596410e215a76a651601901d", "live": true, "id": "x477b6212a24d08da"}',
    u'{"sha": "f6cf4d0675de30afee8cab929b97000e2c41fbc8", "live": true, "id": "xfc8946e7c80f2800"}',
    u'{"sha": "4f522fb965ab3805f56250db187fefadb281edd2", "live": true, "id": "x14784d8f428fa949"}',
    u'{"sha": "849c88aa2122ea5a40bb39540acf551d3ac67728", "live": true, "id": "x3f2d3b6cb53f67a4"}',
    u'{"sha": "a9197ffb73ad014d477c7eb1eed41f9ea025774b", "live": true, "id": "xb6e923d2f396f5ab"}',
    u'{"sha": "446eef76c02fc29049012312c704c12b4b54ba8d", "live": true, "id": "x9ef4ca7e914c87ec"}'
    ]
        
    stuff = json.dumps(thedict)
    
    @set_database
    def setUp(self, db):
        self.db = db
        with Using(db, [Item], with_transaction = False):
            self.item = Item(
                title= self.TITLE, available= self.AVAILABLE, 
                kind = self.KIND,
                description = "test", 
                id = "counting-out-1-20-objects", 
                slug = "test", 
                path = "thepath", 
                extra_fields = self.stuff, 
                all_assessment_items = self.thestuff
                )
            self.item.save()

    def tearDown(self):
        with Using(self.db, [Item], with_transaction = False):    
            self.item.delete_instance()
  

    def test_update_content_availability_true(self):
        expected = {"thepath" :  {'all_assessment_items': [],
            'description': 'test',
            'title': 'testing '}      
        }
    
        with Using(self.db, [Item]):
            actual = dict(update_content_availability([unparse_model_data(model_to_dict(self.item))]))
            self.assertEqual(expected, actual)


    def test_update_content_availability_false(self):
        expected = { "thepath" :  {'all_assessment_items': [],
            'description': 'test',
            'title': 'testing '}      
        }
        with Using(self.db, [Item]):
            actual = dict(update_content_availability([unparse_model_data(model_to_dict(self.item))]))
            self.assertEqual(expected, actual)
