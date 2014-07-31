from django.conf import settings; logging = settings.LOG
from django.core.management.base import BaseCommand

from kalite.topic_tools import video_dict_by_video_id
from ...models import VanillaPlaylist as Playlist


class Command(BaseCommand):
    help = "Check for playlist entries that are invalid and print them to stdout"

    def handle(self, *args, **kwargs):
        video_slugs = set(video_dict_by_video_id().keys())

        for pl in Playlist.all():
            entries = pl.entries
            entry_slugs = set([e['entity_id'] for e in entries if e['entity_kind'] == 'Video'])
            nonexistent_slugs = entry_slugs - video_slugs

            for slug in nonexistent_slugs:
                errormsg = "Video slug in playlist {0} not found in videos: {1}"
                print errormsg.format(pl.id, slug)
