"""
A management command to populate the topic tree from our various json files.
This is a limited-use command meant to transition from the json magic in
topic_tools/__init__.py to using the Django backend. Specifically, it assumes
there's one channel and it's set by settings.CHANNEL.

This management command should be idempotent if the underlying data is the same, which just means
that running twice should be a no-op.
"""
import os
from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

from fle_utils.general import softload_json

from django.conf import settings; logging = settings.LOG
TOPICS_FILEPATHS = {
    settings.CHANNEL: os.path.join(settings.CHANNEL_DATA_PATH, "topics.json")
}
EXERCISES_FILEPATH = os.path.join(settings.CHANNEL_DATA_PATH, "exercises.json")
ASSESSMENT_ITEMS_FILEPATH = os.path.join(settings.CHANNEL_DATA_PATH, "assessmentitems.json")
CONTENT_FILEPATH = os.path.join(settings.CHANNEL_DATA_PATH, "contents.json")

from kalite.topic_tools.models import TopicTreeNode, NodeSubtype, Channel


class Command(BaseCommand):

    def handle(self, *args, **options):
        # Create the one channel.
        khan_ch, found = Channel.objects.get_or_create(language="en", title="khan")

        raw_topics = softload_json(TOPICS_FILEPATHS.get(settings.CHANNEL), logger=logging.debug, raises=False)
        # raw topics is the actual tree structure... have to parse it a node at a time
        def recurse_nodes(raw_node, parent=None):
            """
            Recurse through the raw_topics and create TopicTreeNodes
            :param raw_node: a node from raw_topics
            :param parent: a saved topic_tools.models.TopicTreeNode
            """
            # In general title or description could be absent, but it's probably an error
            # if the other fields are.
            # Just use one object to avoid proliferation, until this field becomes meaningful
            subtype, found = NodeSubtype.objects.get_or_create(pk=1)
            node = TopicTreeNode(
                title=_(raw_node.get("title", "")),
                description=_(raw_node.get("description", "")) if raw_node.get("description") else "",
                slug=raw_node["slug"],
                path=raw_node["path"],
                channel=khan_ch,
                parent=parent,
                node_subtype=subtype
            )
            node.save()
            # Have to reload the parent from the database in order to ensure tree
            # attributes in memory are properly updated.
            if parent:
                parent = TopicTreeNode.objects.get(pk=parent.pk)
            for child in raw_node.get("children", []):
                recurse_nodes(child, node)
        recurse_nodes(raw_topics)