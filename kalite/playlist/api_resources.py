import os
import json
import re
from tastypie import fields
from tastypie.exceptions import NotFound
from tastypie.resources import Resource

from .models import PlaylistToGroupMapping
from kalite.facility.models import FacilityGroup
from kalite.shared.contextmanagers.db import inside_transaction
from kalite.topic_tools import get_flat_topic_tree


class Playlist:
    def __init__(self, **kwargs):
        self.pk = self.id = kwargs.get('id')
        self.title = kwargs.get('title')
        self.description = kwargs.get('description')
        self.groups_assigned = kwargs.get('groups_assigned')


class PlaylistEntry:
    def __init__(self, **kwargs):
        self.entity_id = kwargs.get('entity_id')
        self.entity_kind = kwargs.get('entity_kind')
        self.sort_order = kwargs.get('sort_order')
        self.playlist = kwargs.get('playlist')
        if self.playlist:
            self.pk = self.id = "{}-{}".format(self.playlist.id, self.entity_id)
        else:
            self.pk = self.id = None


class PlaylistResource(Resource):
    playlistjson = os.path.join(os.path.dirname(__file__), 'playlists.json')

    description = fields.CharField(attribute='description')
    id = fields.CharField(attribute='id')
    title = fields.CharField(attribute='title')
    groups_assigned = fields.ListField(attribute='groups_assigned')
    entries = fields.ListField(attribute='entries')

    class Meta:
        resource_name = 'playlist'
        # Use plain python object first instead of full-blown Django ORM model
        object_class = Playlist

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
    def _construct_video_dict():
        # TODO (aron): Add i18n by varying the language of the topic tree here
        topictree = get_flat_topic_tree()

        # since videos in the flat topic tree are indexed by youtube
        # number, we have to construct another dict with the id
        # instead as the key
        video_title_dict = {}
        video_id_regex = re.compile('.*/v/(?P<entity_id>.*)/')
        for video_node in topictree['Video'].itervalues():
            video_id_matches = re.match(video_id_regex, video_node['path'])
            if video_id_matches:
                video_key = video_id_matches.groupdict()['entity_id']
                video_title_dict[video_key] = video_node

        return video_title_dict

    @classmethod
    def _add_full_title_from_topic_tree(cls, entry, video_title_dict):
        # TODO (aron): Add i18n by varying the language of the topic tree here
        topictree = get_flat_topic_tree()

        entry_kind = entry['entity_kind']
        entry_name = entry['entity_id']

        try:
            if entry_kind == 'Exercise':
                entry['description'] = topictree['Exercise'][entry_name]['title']
            if entry_kind == 'Video':
                entry['description'] = video_title_dict[entry_name]['title']
        except KeyError:
            # TODO: edit once we get the properly labeled entity ids from Nalanda
            entry['description'] = entry['entity_id']

        return entry

    def read_playlists(self):
        with open(self.playlistjson) as f:
            raw_playlists = json.load(f)

        # Coerce each playlist dict into a Playlist object
        # also add in the group IDs that are assigned to view this playlist
        playlists = []
        for playlist_dict in raw_playlists:
            playlist = Playlist(title=playlist_dict['title'], description='', id=playlist_dict['id'])

            # instantiate the groups assigned to this playlist
            groups_assigned = FacilityGroup.objects.filter(playlists__playlist=playlist.id).values('id', 'name')
            playlist.groups_assigned = groups_assigned

            # instantiate the playlist entries
            raw_entries = playlist_dict['entries']
            entries = [self._clean_playlist_entry_id(entry) for entry in raw_entries]
            playlist.entries = entries

            playlists.append(playlist)

        return playlists

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}
        if isinstance(bundle_or_obj, Playlist):
            kwargs['pk'] = bundle_or_obj.id
        else:
            kwargs['pk'] = bundle_or_obj.obj.id

        return kwargs

    def get_object_list(self, request):
        '''Get the list of playlists based from a request'''
        return self.read_playlists()

    def obj_get_list(self, bundle, **kwargs):
        return self.get_object_list(bundle.request)

    def obj_get(self, bundle, **kwargs):
        playlists = self.read_playlists()
        pk = kwargs['pk']
        video_dict = self._construct_video_dict()
        for playlist in playlists:
            if str(playlist.id) == pk:
                playlist.entries = [self._add_full_title_from_topic_tree(entry, video_dict) for entry in playlist.entries]
                return playlist
        else:
            raise NotFound('Playlist with pk %s not found' % pk)

    def obj_create(self, request):
        raise NotImplemented("Operation not implemented yet for playlists.")

    def obj_update(self, bundle, **kwargs):
        new_group_ids = set([group['id'] for group in bundle.data['groups_assigned']])
        playlist = Playlist(**bundle.data)

        # hack because playlist isn't a model yet: clear the
        # playlist's groups, then read each one according to what was
        # given in the request. The proper way is to just change the
        # many-to-many relation in the ORM.
        with inside_transaction():
            PlaylistToGroupMapping.objects.filter(playlist=playlist.id).delete()
            new_mappings = ([PlaylistToGroupMapping(group_id=group_id, playlist=playlist.id) for group_id in new_group_ids])
            PlaylistToGroupMapping.objects.bulk_create(new_mappings)

        return bundle

    def obj_delete_list(self, request):
        raise NotImplemented("Operation not implemented yet for playlists.")

    def obj_delete(self, request):
        raise NotImplemented("Operation not implemented yet for playlists.")

    def rollback(self, request):
        raise NotImplemented("Operation not implemented yet for playlists.")
