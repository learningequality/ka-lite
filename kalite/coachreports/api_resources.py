from tastypie import fields
from tastypie.exceptions import NotFound
from tastypie.resources import ModelResource, Resource

from .models import PlaylistProgress, PlaylistProgressDetail

class PlaylistProgressResource(Resource):

    title = fields.CharField(attribute='title')
    id = fields.CharField(attribute='id')
    tag = fields.CharField(attribute='tag', null=True)
    vid_pct_complete = fields.FloatField(attribute='vid_pct_complete')
    vid_pct_started = fields.FloatField(attribute='vid_pct_started')
    ex_pct_mastered = fields.FloatField(attribute='ex_pct_mastered')
    ex_pct_struggling = fields.FloatField(attribute='ex_pct_struggling')
    ex_pct_started = fields.FloatField(attribute='ex_pct_started')
    quiz_exists = fields.BooleanField(attribute='quiz_exists')
    quiz_pct_score = fields.FloatField(attribute='quiz_pct_score')

    class Meta:
        resource_name = "playlist_progress"
        object_class = PlaylistProgress

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}
        if isinstance(bundle_or_obj, PlaylistProgress):
            kwargs['pk'] = bundle_or_obj.id
        else:
            kwargs['pk'] = bundle_or_obj.obj.id

        return kwargs

    def get_object_list(self, request):
        user_id = request.GET.get('user_id')
        result = PlaylistProgress.user_progress(user_id=user_id)
        if not result:
            raise NotFound("User playlist progress with user ID '%s' not found." % user_id)        
        return result

    def obj_get_list(self, bundle, **kwargs):
        return self.get_object_list(bundle.request)


class PlaylistProgressDetailResource(Resource):

    kind = fields.CharField(attribute='kind')
    status = fields.CharField(attribute='status')
    description = fields.CharField(attribute='description')

    class Meta:
        resource_name = "playlist_progress_detail"
        object_class = PlaylistProgressDetail

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}
        if isinstance(bundle_or_obj, PlaylistProgressDetail):
            kwargs['pk'] = bundle_or_obj.id
        else:
            kwargs['pk'] = bundle_or_obj.obj.id

        return kwargs

    def get_object_list(self, request):
        user_id = request.GET.get("user_id")
        playlist_id = request.GET.get("playlist_id")
        result = PlaylistProgressDetail.user_progress_detail(user_id=user_id, playlist_id=playlist_id)
        if not result:
            raise NotFound("User playlist progress details with user ID '%s' and playlist ID '%s' were not found." % (user_id, playlist_id))        
        return result

    def obj_get_list(self, bundle, **kwargs):
        return self.get_object_list(bundle.request)