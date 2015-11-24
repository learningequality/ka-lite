from tastypie import fields
from tastypie.exceptions import NotFound, Unauthorized
from tastypie.resources import Resource

from django.utils.translation import ugettext as _

from kalite.shared.api_auth.auth import UserObjectsOnlyAuthorization
from .models import PlaylistProgress, PlaylistProgressDetail

class CoachReportBaseResource(Resource):
    """
    A base resource that houses shared code between the resources we actually use
    in the API
    """

    class Meta:
        authorization = UserObjectsOnlyAuthorization()

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}
        if isinstance(bundle_or_obj, self._meta.object_class):
            kwargs['pk'] = bundle_or_obj.id
        else:
            kwargs['pk'] = bundle_or_obj.obj.id

        return kwargs

    def obj_get_list(self, bundle, **kwargs):
        return self.get_object_list(bundle.request)


class PlaylistProgressResource(CoachReportBaseResource):

    title = fields.CharField(attribute='title')
    id = fields.CharField(attribute='id')
    tag = fields.CharField(attribute='tag', null=True)
    url = fields.CharField(attribute='url')
    vid_pct_complete = fields.IntegerField(attribute='vid_pct_complete')
    vid_pct_started = fields.IntegerField(attribute='vid_pct_started')
    vid_status = fields.CharField(attribute='vid_status')
    ex_pct_mastered = fields.IntegerField(attribute='ex_pct_mastered')
    ex_pct_struggling = fields.IntegerField(attribute='ex_pct_struggling')
    ex_pct_incomplete = fields.IntegerField(attribute='ex_pct_incomplete')
    ex_status = fields.CharField(attribute='ex_status')
    # quiz_exists = fields.BooleanField(attribute='quiz_exists')
    # quiz_status = fields.CharField(attribute='quiz_status')
    # quiz_pct_score = fields.IntegerField(attribute='quiz_pct_score')
    n_pl_videos = fields.IntegerField(attribute='n_pl_videos')
    n_pl_exercises = fields.IntegerField(attribute='n_pl_exercises')

    class Meta:
        resource_name = "playlist_progress"
        object_class = PlaylistProgress

    def get_object_list(self, request):
        user_id = request.GET.get('user_id')
        result = PlaylistProgress.user_progress(user_id=user_id, language=request.language)
        return result

class PlaylistProgressDetailResource(CoachReportBaseResource):

    kind = fields.CharField(attribute='kind')
    status = fields.CharField(attribute='status')
    title = fields.CharField(attribute='title')
    score = fields.IntegerField(attribute='score')
    path = fields.CharField(attribute='path')

    class Meta:
        resource_name = "playlist_progress_detail"
        object_class = PlaylistProgressDetail

    def get_object_list(self, request):
        user_id = request.GET.get("user_id")
        playlist_id = request.GET.get("playlist_id")
        language = request.language
        result = PlaylistProgressDetail.user_progress_detail(user_id=user_id, playlist_id=playlist_id, language=language)
        if not result:
            raise NotFound("User playlist progress details with user ID '%s' and playlist ID '%s' were not found." % (user_id, playlist_id))
        return result
