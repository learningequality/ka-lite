from mock import patch, MagicMock

import kalite.topic_tools as mod
from kalite.testing.base import KALiteTestCase


DUMMY_STRING = "maize"
TRANS_STRING = "trans"


ugettext_dummy = MagicMock(return_value=DUMMY_STRING)


@patch.object(mod, '_', new=ugettext_dummy)
class SmartTranslateItemDataTests(KALiteTestCase):

    def tearDown(self):
        ugettext_dummy.reset_mock()

    def test_list_of_dicts(self):
        # test_data = {"hints": [{"content": TRANS_STRING, "images": {}, "widgets": {}}]}
        # expected_data = {"hints": [{"content": DUMMY_STRING, "images": {}, "widgets": {}}]}
        self.maxDiff = None
        test_data = {'question': {'content': TRANS_STRING, 'images': {'/content/khan/f24b1c8daf0d1b16bf2dc391393b655e72190290.png': {'width': 450, 'height': 81}}, 'widgets': {'radio 1': {'version': {'major': 0, 'minor': 0}, 'type': 'radio', 'graded': True, 'options': {'onePerLine': True, 'noneOfTheAbove': False, 'choices': [], 'displayCount': None, 'multipleSelect': False, 'randomize': True}}}}, 'answerArea': {'calculator': False, 'type': 'multiple', 'options': {'content': '', 'images': {}, 'widgets': {}}}, 'itemDataVersion': {'major': 0, 'minor': 1}, 'hints': [{'content': TRANS_STRING, 'images': {}, 'widgets': {}}]}
        expected_data = {'question': {'content': DUMMY_STRING, 'images': {'/content/khan/f24b1c8daf0d1b16bf2dc391393b655e72190290.png': {'width': 450, 'height': 81}}, 'widgets': {'radio 1': {'version': {'major': 0, 'minor': 0}, 'type': 'radio', 'graded': True, 'options': {'onePerLine': True, 'noneOfTheAbove': False, 'choices': [], 'displayCount': None, 'multipleSelect': False, 'randomize': True}}}}, 'answerArea': {'calculator': False, 'type': 'multiple', 'options': {'content': '', 'images': {}, 'widgets': {}}}, 'itemDataVersion': {'major': 0, 'minor': 1}, 'hints': [{'content': DUMMY_STRING, 'images': {}, 'widgets': {}}]}

        result = mod.smart_translate_item_data(test_data)
        # ugettext_dummy.assert_called_once_with(TRANS_STRING)

        self.assertEqual(result, expected_data)

    def test_list_of_lists(self):
        test_data = [[TRANS_STRING]]
        expected_data = [[DUMMY_STRING]]

        result = mod.smart_translate_item_data(test_data)
        ugettext_dummy.assert_called_once_with(TRANS_STRING)

        self.assertEqual(result, expected_data)

    def test_simple_content_dict(self):
        # ugettext_method.return_value = DUMMY_STRING
        test_data = {'content': TRANS_STRING}
        expected_data = {'content': DUMMY_STRING}

        result = mod.smart_translate_item_data(test_data)
        ugettext_dummy.assert_called_once_with(TRANS_STRING)

        self.assertEqual(result, expected_data)

    def test_content_in_widgets_field(self):
        test_data = {'widgets': {'content': TRANS_STRING}}
        expected_data = {'widgets': {'content': DUMMY_STRING}}

        result = mod.smart_translate_item_data(test_data)
        ugettext_dummy.assert_called_once_with(TRANS_STRING)

        self.assertEqual(result, expected_data)

    def test_content_inside_radio_field(self):
        test_data = {'radio 1': {'widgets': {'content': TRANS_STRING}}}
        expected_data = {'radio 1': {'widgets': {'content': DUMMY_STRING}}}

        result = mod.smart_translate_item_data(test_data)
        ugettext_dummy.assert_called_once_with(TRANS_STRING)

        self.assertEqual(result, expected_data)

    def test_simple_string(self):
        test_data = TRANS_STRING
        expected_data = DUMMY_STRING

        result = mod.smart_translate_item_data(test_data)
        ugettext_dummy.assert_called_once_with(TRANS_STRING)

        self.assertEqual(result, expected_data)
