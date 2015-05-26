import json
import os

from django.conf import settings; logging = settings.LOG
from django.core.management.base import BaseCommand

from kalite.topic_tools import video_dict_by_video_id, get_node_cache


MALFORMED_IDS = []

class Command(BaseCommand):
    help = "Check for playlist entries that are invalid and print them to stdout"

    def handle(self, *args, **kwargs):

        MALFORMED_IDS = []

        video_slugs = set(video_dict_by_video_id().keys())
        exercise_slugs = set(get_node_cache()["Exercise"].keys())

        all_playlists = json.load(open(os.path.join(settings.PROJECT_PATH, 'playlist/playlists.json')))

        # for pl in Playlist.all():
        for pl in all_playlists:
            # entries = pl.entries
            entries = pl.get("entries")

            # Find video ids in the playlists that are not in the topic tree
            video_entry_slugs = [enforce_and_strip_slug(pl.get("id"), e['entity_id']) for e in entries if e['entity_kind'] == 'Video']
            nonexistent_video_slugs = set(filter(None, video_entry_slugs)) - video_slugs

            # Find exercise ids in the playlists that are not in the topic tree
            ex_entry_slugs = [enforce_and_strip_slug(pl.get("id"), e['entity_id']) for e in entries if e['entity_kind'] == 'Exercise']
            nonexistent_ex_slugs = set(filter(None, ex_entry_slugs)) - exercise_slugs

            # Print malformed videos
            for slug in nonexistent_video_slugs:
                errormsg = "Video slug in playlist {0} not found in videos: {1}"
                # print errormsg.format(pl.id, slug)
                print errormsg.format(pl.get("id"), slug)

            # Print malformed exercises
            for slug in nonexistent_ex_slugs:
                errormsg = "Exercise slug in playlist {0} not found in exercises: {1}"
                # print errormsg.format(pl.id, slug)
                print errormsg.format(pl.get("id"), slug)

            # Print misspelled ids
            for m in MALFORMED_IDS:
                errormsg = "Malformed slug in playlist {0}. Please investigate: {1}"
                # print errormsg.format(pl.id, slug)
                print errormsg.format(pl.get("id"), m)
            MALFORMED_IDS = []

def enforce_and_strip_slug(playlist_id, slug):
        split_slug = [x for x in slug.split("/") if len(x) > 1]
        if len(split_slug) != 1:
            print "Malformed slug in playlist %s, slug: %s" % (playlist_id, slug)
        else:
            return split_slug[0]
