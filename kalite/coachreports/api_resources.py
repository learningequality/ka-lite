from tastypie import fields
from tastypie.exceptions import NotFound, Unauthorized
from tastypie.resources import ModelResource, Resource
from tastypie.utils import now

from django.db.models import Sum, Count
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse

from kalite.shared.decorators import get_user_from_request
from .models import PlaylistProgress, PlaylistProgressDetail

from kalite.facility.api_resources import FacilityUserResource
from kalite.shared.api_auth import UserObjectsOnlyAuthorization
from kalite.main.models import ExerciseLog
from copy import deepcopy

from kalite.topic_tools import get_exercise_cache

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

class ExerciseSummaryResource(ModelResource):
    user = fields.ForeignKey(FacilityUserResource, 'user')

    def obj_create(self, bundle, **kwargs):
        is_admin = getattr(bundle.request, "is_admin", False)
        user = getattr(bundle.request, "user", None)
        if is_admin:
            if user and getattr(user, 'is_superuser', False):
                return None
        return super(ExerciseLogResource, self).obj_create(bundle, **kwargs)

class ScatterReportExerciseResource(ExerciseSummaryResource):

    class Meta:
        queryset = ExerciseLog.objects.all()
        resource_name = 'ScatterReportExerciselog'
        excludes = ['attempts_before_completion', 
            'complete', 'counter', 'attempts', 'signed_version', 'signature', 'resource_uri', 'id', 'language', 
            'resource_uri', 'user', 'streak_progress', 'points', 'completion_counter', 'completion_timestamp',
            'exercise_id', 'mastered', 'struggling', 'deleted'
            ]
        # filtering = {
        #     # "exercise_id": ('exact', ),
        #     # "user": ('exact', ),
        #     "completion_timestamp": ('gte', 'lte')
        # }
        authorization = UserObjectsOnlyAuthorization()

    # add this custom field to store all the info needed for scatter report
    user_info = []
    # dehydrate() can add extra field to the result json without change the model
    # dehydrate() will get called as many times as how many objects exist in the queryset
    def dehydrate(self, bundle): 
        userinfo = self.user_info.pop()
        bundle.data['user_name'] = userinfo.get('user_name')
        bundle.data['total_attempts'] = userinfo.get('total_attempts')
        bundle.data['mastered'] = userinfo.get('mastered')
        bundle.data['exercises'] = userinfo.get('exercises')
        return bundle

    def get_object_list(self, request):
        #TODO-BLOCKER(66eli77): need to find a way to include exercises that are not completed yet.
        if not request.GET.get('facility_id'):
            if not request.GET.get('group_id'):
                return super(ExerciseSummaryResource, self).get_object_list(request).filter(
                    completion_timestamp__gte=request.GET.get('completion_timestamp__gte'), 
                    completion_timestamp__lte=request.GET.get('completion_timestamp__lte'))
            else:
                return super(ExerciseSummaryResource, self).get_object_list(request).filter(
                    completion_timestamp__gte=request.GET.get('completion_timestamp__gte'), 
                    completion_timestamp__lte=request.GET.get('completion_timestamp__lte'),
                    user__group=request.GET.get('group_id'))
        else:
            if not request.GET.get('group_id'):
                return super(ExerciseSummaryResource, self).get_object_list(request).filter(
                    completion_timestamp__gte=request.GET.get('completion_timestamp__gte'), 
                    completion_timestamp__lte=request.GET.get('completion_timestamp__lte'),
                    user__facility=request.GET.get('facility_id'))
            else:
                return super(ExerciseSummaryResource, self).get_object_list(request).filter(
                    completion_timestamp__gte=request.GET.get('completion_timestamp__gte'), 
                    completion_timestamp__lte=request.GET.get('completion_timestamp__lte'),
                    user__facility=request.GET.get('facility_id'),
                    user__group=request.GET.get('group_id'))

    def obj_get_list(self, bundle, **kwargs):
        # self.permission_check(bundle.request)
        exercise_logs = self.get_object_list(bundle.request)
        pre_user = None
        filtered_logs = []
        exercises_info = []

        for e in exercise_logs:
            if e.user == pre_user:
                pass
            else:
                pre_user = e.user
                attempts = exercise_logs.filter(user=e.user).aggregate(Sum("attempts"))["attempts__sum"]
                mastered = exercise_logs.filter(user=e.user, complete=True).count()
                exercises_info = exercise_logs.filter(user=e.user).values('exercise_id', 'attempts', 'struggling')
                for i in exercises_info:
                    i["exercise_url"] = get_exercise_cache().get(i['exercise_id']).get("path")

                user_dic = {
                    "user_name": e.user.get_name(),
                    "total_attempts": attempts,
                    "mastered": mastered,
                    "exercises": list(exercises_info)
                }
                filtered_logs.append(e)
                self.user_info.append(user_dic)

        self.user_info.reverse()
        return filtered_logs

class TimelineReportExerciseResource(ExerciseSummaryResource):

    class Meta:
        queryset = ExerciseLog.objects.all()
        resource_name = 'TimelineReportExerciselog'
        excludes = ['attempts_before_completion', 
            'complete', 'counter', 'attempts', 'signed_version', 'signature', 'resource_uri', 'id', 'language', 
            'resource_uri', 'user', 'streak_progress', 'points', 'completion_counter', 'completion_timestamp',
            'exercise_id', 'mastered', 'struggling', 'deleted'
            ]
        # filtering = {
        #     # "exercise_id": ('exact', ),
        #     # "user": ('exact', ),
        #     "completion_timestamp": ('gte', 'lte')
        # }
        authorization = UserObjectsOnlyAuthorization()

    # add this custom field to store all the info needed for scatter report
    user_info = []
    # dehydrate() can add extra field to the result json without change the model
    # dehydrate() will get called as many times as how many objects exist in the queryset
    def dehydrate(self, bundle): 
        userinfo = self.user_info.pop()
        bundle.data['user_name'] = userinfo.get('user_name')
        bundle.data['total_attempts'] = userinfo.get('total_attempts')
        bundle.data['mastered'] = userinfo.get('mastered')
        bundle.data['exercises'] = userinfo.get('exercises')
        return bundle

    def get_object_list(self, request):
        #TODO-BLOCKER(66eli77): need to find a way to include exercises that are not completed yet.
        if not request.GET.get('facility_id'):
            if not request.GET.get('group_id'):
                return super(ExerciseSummaryResource, self).get_object_list(request).filter(
                    completion_timestamp__gte=request.GET.get('completion_timestamp__gte'), 
                    completion_timestamp__lte=request.GET.get('completion_timestamp__lte'))
            else:
                return super(ExerciseSummaryResource, self).get_object_list(request).filter(
                    completion_timestamp__gte=request.GET.get('completion_timestamp__gte'), 
                    completion_timestamp__lte=request.GET.get('completion_timestamp__lte'),
                    user__group=request.GET.get('group_id'))
        else:
            if not request.GET.get('group_id'):
                return super(ExerciseSummaryResource, self).get_object_list(request).filter(
                    completion_timestamp__gte=request.GET.get('completion_timestamp__gte'), 
                    completion_timestamp__lte=request.GET.get('completion_timestamp__lte'),
                    user__facility=request.GET.get('facility_id'))
            else:
                return super(ExerciseSummaryResource, self).get_object_list(request).filter(
                    completion_timestamp__gte=request.GET.get('completion_timestamp__gte'), 
                    completion_timestamp__lte=request.GET.get('completion_timestamp__lte'),
                    user__facility=request.GET.get('facility_id'),
                    user__group=request.GET.get('group_id'))

    def obj_get_list(self, bundle, **kwargs):
        # self.permission_check(bundle.request)
        exercise_logs = self.get_object_list(bundle.request)
        pre_user = None
        filtered_logs = []
        exercises_info = []

        for e in exercise_logs:
            if e.user == pre_user:
                pass
            else:
                pre_user = e.user
                attempts = exercise_logs.filter(user=e.user).aggregate(Sum("attempts"))["attempts__sum"]
                mastered = exercise_logs.filter(user=e.user, complete=True).count()
                exercises_info = exercise_logs.filter(user=e.user).values('exercise_id', 'attempts', 'struggling')
                for i in exercises_info:
                    i["exercise_url"] = get_exercise_cache().get(i['exercise_id']).get("path")

                user_dic = {
                    "user_name": e.user.get_name(),
                    "total_attempts": attempts,
                    "mastered": mastered,
                    "exercises": list(exercises_info)
                }
                filtered_logs.append(e)
                self.user_info.append(user_dic)

        self.user_info.reverse()
        return filtered_logs