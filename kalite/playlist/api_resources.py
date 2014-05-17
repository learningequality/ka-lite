import os
import json

from tastypie import fields
from tastypie.exceptions import NotFound
from tastypie.resources import ModelResource, Resource

from .models import Playlist, PlaylistEntry, PlaylistToGroupMapping


class PlaylistResource(Resource):
    playlistjson = os.path.join(os.path.dirname(__file__), 'test_playlist.json')

    description = fields.CharField(attribute='description')
    id = fields.CharField(attribute='id')
    title = fields.CharField(attribute='title')

    class Meta:
        resource_name = 'playlist'
        object_class = Playlist

    def read_playlists(self):
        with open(self.playlistjson) as f:
            raw_playlists = json.load(f)

        # Coerce each playlist dict into a Playlist object
        # also add in the group IDs that are assigned to view this playlist
        playlists = []
        for playlist_dict in raw_playlists:
            playlist = Playlist(title=playlist_dict['title'], description='', id=playlist_dict['id'])
            groups_assigned = PlaylistToGroupMapping.objects.filter(playlist=playlist_dict['id']).values('group')
            playlist.groups_assigned = groups_assigned
            playlists.append(playlist)

        return playlists

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}
        if isinstance(bundle_or_obj, Playlist):
            kwargs['id'] = bundle_or_obj.id
        else:
            kwargs['id'] = bundle_or_obj.obj.id

        return kwargs

    def get_object_list(self, request):
        '''Get the list of playlists based from a request'''
        return self.read_playlists()

    def obj_get_list(self, bundle, **kwargs):
        return self.get_object_list(bundle.request)

    def obj_get(self, bundle, **kwargs):
        playlists = self.read_playlists()
        pk = kwargs['pk']
        for playlist in playlists:
            if str(playlist.id) == pk:
                return playlist
        else:
            raise NotFound('Playlist with pk %s not found' % pk)

    def obj_create(self, request):
        raise NotImplemented("Operation not implemented yet for playlists.")

    def obj_update(self, request):
        raise NotImplemented("Operation not implemented yet for playlists.")

    def obj_delete_list(self, request):
        raise NotImplemented("Operation not implemented yet for playlists.")

    def obj_delete(self, request):
        raise NotImplemented("Operation not implemented yet for playlists.")

    def rollback(self, request):
        raise NotImplemented("Operation not implemented yet for playlists.")


class PlaylistEntryResource(ModelResource):
    playlist = fields.ForeignKey(PlaylistResource, 'playlist')

    class Meta:
        queryset = PlaylistEntry.objects.all()
        resource_name = 'playlist_entry'
