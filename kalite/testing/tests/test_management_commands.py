import os
import platform
import sys
import unittest
import importlib

from django.core.management.base import CommandError
from fle_utils.django_utils import call_command_with_output

class ModelCreationCommandTests(unittest.TestCase):
    def test_no_args(self):
        try:
            (out, err, rc) = call_command_with_output('createmodel')
            self.assertFail()
        except CommandError as e:
            self.assertRegexpMatches(str(e), "No args specified")

    def test_no_options(self):
        try:
            (out, err, rc) = call_command_with_output('createmodel', 'some.model')
            self.assertFail()
        except CommandError as e:
            self.assertRegexpMatches(str(e), 
                                     "Please specifiy input data as a json string")

    def test_save_model(self):
        MODEL_NAME = 'kalite.facility.models.Facility'
        (out, err, rc) = call_command_with_output('createmodel',
                                                  MODEL_NAME,
                                                  json_data='{"name" : "kir1"}')
        self.assertEquals(rc, 0)
        module_path, model_name = MODEL_NAME.rsplit(".", 1)
        module = importlib.import_module(module_path)
        model = getattr(module, model_name)

        data = model.objects.get(pk=out.strip())
        self.assertEquals(data.name, "kir1")
        
