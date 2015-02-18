from fle_utils.django_utils.templatetags.my_filters import jsonify

from django.core.exceptions import ValidationError
from django.test import TestCase

from kalite.dynamic_assets import DynamicSettingsBase, fields


class DynamicSettingsModelsTests(TestCase):

    def test_can_define_new_dynamic_setting_instance(self):

        class DynamicSettings(DynamicSettingsBase):
            test_intsetting = fields.IntegerField(default=17, minimum=0, maximum=20)
            test_charsetting = fields.CharField(default="This is a test.")
            test_boolsetting = fields.BooleanField(default=True)

        s = DynamicSettings()

    def test_default_values_are_being_used(self):

        class DynamicSettings(DynamicSettingsBase):
            test_intsetting = fields.IntegerField(default=17, minimum=0, maximum=20)
            test_charsetting = fields.CharField(default="This is a test.")
            test_boolsetting = fields.BooleanField(default=True)

        s = DynamicSettings()

        self.assertEqual(s.test_intsetting, 17)
        self.assertEqual(s.test_charsetting, "This is a test.")
        self.assertEqual(s.test_boolsetting, True)

    def test_ds_must_be_json_serializable(self):

        class DynamicSettings(DynamicSettingsBase):
            test_intsetting = fields.IntegerField(default=17, minimum=0, maximum=20)
            test_charsetting = fields.CharField(default="This is a test.")
            test_boolsetting = fields.BooleanField(default=True)

        s = DynamicSettings()

        self.assertTrue("This is a test." in jsonify(s))

    def test_ds_fields_are_not_leaky_across_instances(self):

        class DynamicSettings(DynamicSettingsBase):
            test_intsetting = fields.IntegerField(default=17, minimum=0, maximum=20)
            test_charsetting = fields.CharField(default="This is a test.")
            test_boolsetting = fields.BooleanField(default=True)

        s1 = DynamicSettings()
        s1.test_charsetting = "My personal value."

        s2 = DynamicSettings()

        self.assertEqual(s2.test_charsetting, "This is a test.")


class FieldValidationTests(TestCase):

    def test_cant_instantiate_a_basefield(self):

        with self.assertRaises(NotImplementedError):
            fields.BaseField()

    def test_invalid_intfield_raises_error(self):

        class DynamicSettings(DynamicSettingsBase):
            test_intsetting = fields.IntegerField(default=True, minimum=0, maximum=20)
            test_charsetting = fields.CharField(default=17)
            test_boolsetting = fields.BooleanField(default="This is a test.")

        s = DynamicSettings()

        try:
            s.validate()
        except ValidationError as e:
            self.assertTrue("test_intsetting" in e.message_dict, "Validation did not work for IntegerField.")
            self.assertTrue("test_charsetting" in e.message_dict, "Validation did not work for CharField.")
            self.assertTrue("test_boolsetting" in e.message_dict, "Validation did not work for BooleanField.")
        else:
            # exception wasn't thrown, so complain about that
            with self.assertRaises(ValidationError):
                s.validate()
