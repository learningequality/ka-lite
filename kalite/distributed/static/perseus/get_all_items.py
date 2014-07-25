#!/usr/bin/python
import json
from contextlib import closing
import urllib2
import base64
import re
import getpass
import datetime

tags = {}
item_ids = []
items = {}

req = urllib2.Request("https://www.khanacademy.org/api/v1/assessment_items/tags?format=pretty")
with closing(urllib2.urlopen(req)) as tag_data:
    all_tags = json.loads(tag_data.read().decode('utf-8'))
    for tag in all_tags:
        tags[tag['id']] = tag['display_name']

req = urllib2.Request("https://www.khanacademy.org/api/v1/exercises")
with closing(urllib2.urlopen(req)) as exercise_data:
    exercises = json.loads(exercise_data.read().decode('utf-8'))
    for exercise in exercises:
        if (not exercise['deleted'] and exercise['uses_assessment_items']):
            for problem_type in exercise['problem_types']:
                for item in problem_type['items']:
                    item_ids += [item['id']]


for n, item_id in enumerate(item_ids):
    while True:  # never, never, never give up
        try:
            req = urllib2.Request("https://www.khanacademy.org/api/v1/assessment_items/" + item_id)
            with closing(urllib2.urlopen(req)) as item_data:
                item = json.loads(item_data.read().decode('utf-8'))

                # replace tag keys with tag names
                for i, tag_key in enumerate(item['tags']):
                    item['tags'][i] = tags[tag_key]

                # replace item_data string with json
                item['item_data'] = json.loads(item['item_data'])

                items[item['id']] = item

        except:
            print "retrying..."
            continue
        break

    print "%d / %d" % (n + 1, len(item_ids))


item_file = open("items.json", "w")
json.dump(items, item_file)

