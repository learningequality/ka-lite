import json
import os
import tempfile
import string
import random
import shutil
import operator

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.core.urlresolvers import reverse
from django.utils import unittest

from kalite.main.tests.base import MainTestCase
from kalite.contentload.management.commands.channels import import_channel

from fle_utils.general import ensure_dir


class TestContentImportTopicTree(MainTestCase):

    extensions = [("pdf", "Document"), ("mp3", "Audio"), ("mp4", "Video")]
    metadata = ["title", "description", "author", "language"]

    def setUp(self, *args, **kwargs):
        """
        Create a temporary directory.
        """
        super(TestContentImportTopicTree, self).setUp(*args, **kwargs)
        self.tempdir = tempfile.mkdtemp()
        self.recursion_depth = 0
        self.channel = {
            "id": "test",
            "path": os.path.join(settings.CONTENT_DATA_PATH, "test")
        }


    def tearDown(self, *args, **kwargs):
        """
        Remove temporary directory.
        """
        super(TestContentImportTopicTree, self).tearDown(*args, **kwargs)
        shutil.rmtree(self.tempdir)

    def create_node(self, path):
        filename = "".join(random.sample(string.lowercase, 16))
        data = {}
        for metadatum in self.metadata:
            data[metadatum] = "".join(random.sample(string.lowercase, 16))
        if random.random() > 0.5:
            filetype = random.choice(self.extensions)
            extension = filetype[0]
            filekind = filetype[1]
            with open(os.path.join(os.path.dirname(self.tempdir), path, filename + ".%s" % extension), 'w') as f:
                f.write(str(random.random()))
            with open(os.path.join(os.path.dirname(self.tempdir), path, filename + ".%s" % extension + ".json"), 'w') as f:
                json.dump(data, f)
            data["kind"] = filekind
            data["format"] = extension
        else:
            ensure_dir(os.path.join(os.path.dirname(self.tempdir), path, filename))
            with open(os.path.join(os.path.dirname(self.tempdir), path, filename + ".json"), 'w') as f:
                json.dump(data, f)
            data["kind"] = "Topic"
            data["children"] = []
        data["path"] = os.path.join(path, filename)
        data["slug"] = filename
        return data

    def recursively_create_nodes(self, node):
        self.recursion_depth += 1
        if node["kind"] == "Topic":
            for i in range(0,5):
                child = self.create_node(node["path"])
                node["children"].append(child)
                if self.recursion_depth < 6:
                    self.recursively_create_nodes(child)
            node["children"] = sorted(node["children"], key=operator.itemgetter("slug"))
        self.recursion_depth -= 1

    def recursively_test_nodes(self, source, generated):
        for key, value in source.items():
            if key != "children":
                self.assertEqual(value, generated.get(key, ""))
            else:
                generated["children"] = sorted(generated["children"], key=operator.itemgetter("slug"))
                for i, node in enumerate(value):
                    self.recursively_test_nodes(node, generated.get(key, [])[i])

    def test_create_topic_tree(self):
        topic_tree = {
            "slug": os.path.basename(self.tempdir),
            "children": [],
            "kind": "Topic",
            "path": os.path.basename(self.tempdir),
        }
        self.recursively_create_nodes(topic_tree)
        import_channel.path = self.tempdir
        generated_topic_tree, exercises, videos, assessment_items, content = import_channel.retrieve_API_data(self.channel)

        self.recursively_test_nodes(topic_tree, generated_topic_tree)
