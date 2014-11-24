from tastypie import fields
from tastypie.exceptions import NotFound, Unauthorized
from tastypie.resources import ModelResource, Resource

from django.utils.translation import ugettext as _

from kalite.shared.decorators import get_user_from_request
from .models import PlaylistProgress, PlaylistProgressDetail


class PlaylistParentResource(Resource):
    """
    A parent resource that houses shared code between the two resources we actually use 
    in the API
    """

    @classmethod
    def permission_check(self, request):
        """
        Require that the users are logged in, and that the user is the same student 
        whose data is being requested, an admin, or a teacher in that facility
        """
        if getattr(request, "is_logged_in", False):  
            pass
        else:
            raise Unauthorized(_("You must be logged in to access this page."))

        if getattr(request, "is_admin", False):
            pass
        else:
            user = get_user_from_request(request=request)
            if request.GET.get("user_id") == user.id:
                pass
            else:
                raise Unauthorized(_("You requested information for a user that you are not authorized to view."))


class PlaylistProgressResource(PlaylistParentResource):

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
    quiz_exists = fields.BooleanField(attribute='quiz_exists')
    quiz_status = fields.CharField(attribute='quiz_status')
    quiz_pct_score = fields.IntegerField(attribute='quiz_pct_score')
    n_pl_videos = fields.IntegerField(attribute='n_pl_videos')
    n_pl_exercises = fields.IntegerField(attribute='n_pl_exercises')

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
        return result

    def obj_get_list(self, bundle, **kwargs):
        self.permission_check(bundle.request)
        return self.get_object_list(bundle.request)


class PlaylistProgressDetailResource(PlaylistParentResource):

    kind = fields.CharField(attribute='kind')
    status = fields.CharField(attribute='status')
    title = fields.CharField(attribute='title')
    score = fields.IntegerField(attribute='score')
    path = fields.CharField(attribute='path')

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
        self.permission_check(bundle.request)
        return self.get_object_list(bundle.request)