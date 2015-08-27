import json
import os
import tempfile
import string
import random
import shutil
import operator

from django.conf import settings

from kalite.main.tests.base import MainTestCase
from kalite.contentload.management.commands.channels import import_channel, base

from fle_utils.general import ensure_dir
import unittest


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
            "id": os.path.basename(self.tempdir),
            "path": os.path.join(settings.CONTENT_DATA_PATH, os.path.basename(self.tempdir)),
            "name": os.path.basename(self.tempdir),
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
        data["slug"] = filename
        data["path"] = os.path.join(path, data["slug"])
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
                if key == "slug" or key == "path":
                    value = unicode(value.lower())
                self.assertEqual(value, generated.get(key, ""), "{key} not equal to generated {key}, {value} not equal {genvalue}".format(key=key, value=value, genvalue=generated.get(key, "")))
            else:
                generated["children"] = sorted(generated["children"], key=operator.itemgetter("slug"))
                for i, node in enumerate(value):
                    self.recursively_test_nodes(node, generated.get(key, [])[i])

    def recursively_find_nodes(self, node, key, value, cache):
        if key in node:
            if node[key] == value:
                cache.append(node)
        if "children" in node:
            for child in node["children"]:
                self.recursively_find_nodes(child, key, value, cache)

    @unittest.skip("Skipping until kaa package is replaced")
    def test_create_topic_tree(self):
        slug = os.path.basename(self.tempdir)
        topic_tree = {
            "slug": slug,
            "children": [],
            "kind": "Topic",
            "path": slug,
        }
        self.recursively_create_nodes(topic_tree)
        import_channel.path = self.tempdir
        generated_topic_tree, exercises, assessment_items, content = import_channel.retrieve_API_data(self.channel)

        self.recursively_test_nodes(topic_tree, generated_topic_tree)

    def test_rebuild_topic_tree_not_delete_videos(self):
        topic_tree = {
            "slug": os.path.basename(self.tempdir),
            "children": [],
            "kind": "Topic",
            "path": os.path.basename(self.tempdir),
        }
        self.recursively_create_nodes(topic_tree)
        node_cache = []
        self.recursively_find_nodes(topic_tree, "kind", "Video", node_cache)

        retrieve_API_data = lambda channel: (topic_tree, [], [], [])

        topic_tree, exercises, assessment_items, contents = base.rebuild_topictree(whitewash_node_data=import_channel.whitewash_node_data, retrieve_API_data=retrieve_API_data, channel_data=import_channel.channel_data)

        new_node_cache = []
        self.recursively_find_nodes(topic_tree, "kind", "Video", new_node_cache)

        self.assertEqual(node_cache, new_node_cache, "Rebuild Topictree deletes videos!")