import copy
import json
import re
import requests

from django.core.management.base import NoArgsCommand


class Command(NoArgsCommand):

    def handle_noargs(self, **options):
        assessment_items_url = "https://s3.amazonaws.com/uploads.hipchat.com/86198%2F624195%2FtYo7Ez0tt3e1qQW%2Fassessmentitems.json"
        assessment_items = json.loads(requests.get(assessment_items_url).content)


def all_image_urls(items):
    for _, v in items.iteritems():

        item_data = v["item_data"]
        imgurlregex = r'http.*?\.png'

        for match in re.finditer(imgurlregex, item_data):
            yield str(match.group(0))  # match.group(0) means get the entire string


def localhosted_image_urls(items):
    newitems = copy.deepcopy(items)

    url_to_replace = r'https://ka-perseus-graphie.s3.amazonaws.com/(?P<id>\w+)\.png'

    for _, v in newitems.iteritems():
        old_item_data = v['item_data']
        v['item_data'] = re.sub(url_to_replace, r'http://localhost:8008/\g<id>.png', old_item_data)

    return newitems
