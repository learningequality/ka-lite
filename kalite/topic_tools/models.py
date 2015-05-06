from mptt.models import MPTTModel, TreeForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models

class Channel(models.Model):
    language = models.CharField(max_length=8)
    title = models.CharField(max_length=50)

class TopicTreeNode(MPTTModel):
    title = models.CharField(max_length=50)
    description = models.CharField(max_length=50)
    slug = models.SlugField(max_length=255, primary_key=True, unique=True)
    path = models.URLField(max_length=200, unique=True)
    channel = models.ForeignKey('Channel')
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)

    # The "kind" of the node
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    node_subtype = generic.GenericForeignKey('content_type', 'object_id')

class NodeSubtype(models.Model):
    pass