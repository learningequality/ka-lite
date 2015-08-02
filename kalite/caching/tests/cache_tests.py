"""
Test the topic-tree caching code (but only if caching is enabled in settings)
"""
import random
import requests
import urllib

from django.conf import settings; logging = settings.LOG
from django.test.client import Client
from django.utils import unittest

from .. import caching
from kalite.testing.base import KALiteTestCase
from kalite.topic_tools import get_content_cache


class CachingTest(KALiteTestCase):
    content_cache = get_content_cache()
