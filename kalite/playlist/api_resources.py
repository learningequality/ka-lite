from tastypie import fields
from tastypie.resources import ModelResource

from kalite.facility.models import FacilityUser

from .models import Playlist, PlaylistEntry


class PlaylistResource(ModelResource):
    class Meta:
        queryset = Playlist.objects.all()
        resource_name = 'playlist'


class PlaylistEntryResource(ModelResource):
    playlist = fields.ForeignKey(PlaylistResource, 'playlist')

    class Meta:
        queryset = PlaylistEntry.objects.all()
        resource_name = 'playlist_entry'
