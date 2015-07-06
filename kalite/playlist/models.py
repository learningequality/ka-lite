import json
import os
from django.db import models
from django.conf import settings

from fle_utils.django_utils.classes import ExtendedModel

from kalite.facility.models import FacilityGroup, FacilityUser
from kalite.topic_tools import get_node_cache

from securesync.models import DeferredCountSyncedModel


class Playlist(ExtendedModel):
    title = models.CharField(max_length=30)
    description = models.TextField(blank=True)

    def __unicode__(self):
        return "%(title)s:%(desc)s" % {'title': self.title, 'desc': self.description}

    def add_entry(self, *args, **kwargs):
        '''
        Add a playlist entry to the playlist. Automatically inserts the
        right sort order number, and moves other playlist entries if
        inserting an entry in the middle, aka adding an entry with an
        already existing sort order.

        '''
        if 'sort_order' not in kwargs:  # by default, append entry to the playlist
            try:
                last_entry = self.entries.order_by('-sort_order').all()[0]
                kwargs['sort_order'] = last_entry.sort_order + 1
            except IndexError:  # no entries yet
                kwargs['sort_order'] = 0
        else:
            num_entries = self.entries.count()
            entries_to_move = self.entries.filter(
                sort_order__gte=kwargs['sort_order']
            )
            if num_entries > 0 and entries_to_move.exists():
                entries_to_move.update(sort_order=models.F('sort_order') + 1)

        return self.entries.create(*args, **kwargs)


class PlaylistEntry(ExtendedModel):
    ENTITY_KINDS = (
        ('Video', 'Video'),
        ('Exercise', 'Exercise'),
        ('Quiz', 'Quiz'),
        ('Divider', 'Divider'),
    )

    entity_kind = models.CharField(max_length=10, choices=ENTITY_KINDS)
    entity_id = models.CharField(max_length=50)
    sort_order = models.IntegerField()
    description = models.TextField()
    playlist = models.ForeignKey(Playlist, related_name='entries')

    class Meta:
        ordering = ['playlist', 'sort_order']


class PlaylistToGroupMapping(ExtendedModel):
    playlist = models.CharField(db_index=True, max_length=15)
    group = models.ForeignKey(FacilityGroup, related_name='playlists')


class QuizLog(DeferredCountSyncedModel):

    minversion = "0.13.0"

    user = models.ForeignKey(FacilityUser, blank=False, null=False, db_index=True)
    quiz = models.CharField(blank=True, max_length=100)
    index = models.IntegerField(blank=False, null=False, default=0)
    complete = models.BooleanField(blank=False, null=False, default=False)
    # Attempts is the number of times the Quiz itself has been attempted.
    attempts = models.IntegerField(blank=False, null=False, default=0)
    total_number = models.IntegerField(blank=False, null=False, default=0)
    total_correct = models.IntegerField(blank=False, null=False, default=0)
    response_log = models.TextField(default="[]")

    class Meta:  # needed to clear out the app_name property from SyncedClass.Meta
        pass


class VanillaPlaylist:
    """
    A simple playlist object that just loads from a playlists json file. Contrast
    with Playlist, which is a Django model.
    """
    playlistjson = os.path.join(os.path.dirname(__file__), 'playlists.json')

    __slots__ = ['pk', 'id', 'title', 'description', 'groups_assigned', 'unit', 'show']

    def __init__(self, **kwargs):
        self.pk = self.id = kwargs.get('id')
        self.title = kwargs.get('title')
        self.tag = kwargs.get('tag')
        self.description = kwargs.get('description')
        self.groups_assigned = kwargs.get('groups_assigned')
        self.unit = kwargs.get('unit')

    @classmethod
    def all(cls, limit_to_shown=True):
        if "nalanda" not in settings.CONFIG_PACKAGE:
            return []

        with open(cls.playlistjson) as f:
            raw_playlists = json.load(f)

        # Coerce each playlist dict into a Playlist object
        # also add in the group IDs that are assigned to view this playlist
        playlists = []
        for playlist_dict in raw_playlists:
            # don't include playlists without show: True attribute
            if limit_to_shown and not playlist_dict.get("show"):
                continue

            playlist = cls(title=playlist_dict['title'],
                           description='',
                           show=playlist_dict.get('show', False),
                           id=playlist_dict['id'],
                           tag=playlist_dict['tag'],
                           unit=playlist_dict['unit'])

            # instantiate the groups assigned to this playlist
            groups_assigned = FacilityGroup.objects.filter(playlists__playlist=playlist.id).values('id', 'name')
            playlist.groups_assigned = groups_assigned

            # instantiate the playlist entries
            raw_entries = playlist_dict['entries']
            playlist.entries = [VanillaPlaylistEntry._clean_playlist_entry_id(e) for e in raw_entries]

            playlists.append(playlist)

        return playlists

    def get_playlist_entries(playlist, entry_type, language=None):
        """
        Given a VanillaPlaylist, inspect its 'entries' attribute and return a list
        containing corresponding nodes for each item from the topic tree.
        entry_type should be "Exercise" or "Video".
        """
        if not language:
            language = settings.LANGUAGE_CODE

        unprepared = filter(lambda e: e["entity_kind"]==entry_type, playlist.entries)
        prepared = []
        for entry in unprepared:
            new_item = get_node_cache(language=language)[entry_type].get(entry['entity_id'], None)
            if new_item:
                prepared.append(new_item)
        return prepared

class VanillaPlaylistEntry:
    """
    A plain object that models playlist entries. Contrast with PlaylistEntry,
    which is a Django model. For now, it's just a collection of static methods
    for operating on playlist entry dictionaries.
    """

    @staticmethod
    def _clean_playlist_entry_id(entry):
        name = entry['entity_id']
        # strip any trailing whitespace
        name = name.strip()

        # try to extract only the actual entity id
        name_breakdown = name.split('/')
        name_breakdown = [
            component for component
            in name.split('/')
            if component  # make sure component has something in it
        ]
        name = name_breakdown[-1]

        entry['old_entity_id'] = entry['entity_id']
        entry['entity_id'] = name

        return entry

    @staticmethod
    def add_full_title_from_topic_tree(entry, video_title_dict):
        # TODO (aron): Add i18n by varying the language of the topic tree here
        topictree = get_node_cache()

        entry_kind = entry['entity_kind']
        entry_name = entry['entity_id']

        try:
            if entry_kind == 'Exercise':
                nodedict = topictree['Exercise']
            elif entry_kind == 'Video':
                # TODO-blocker: move use of video_dict_by_id to slug2id_map
                nodedict = video_title_dict
            else:
                nodedict = {}

            entry['title'] = nodedict[entry_name]['title']
            entry['description'] = nodedict[entry_name].get('description', '')
        except KeyError:
            # TODO: edit once we get the properly labeled entity ids from Nalanda
            entry['title'] = entry['description'] = entry['entity_id']

        return entry
