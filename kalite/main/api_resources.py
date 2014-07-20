from tastypie import fields
from tastypie.resources import ModelResource, Resource
from tastypie.exceptions import NotFound

from django.utils.translation import ugettext as _
from django.conf.urls import url

from .models import ExerciseLog, AttemptLog

from kalite.topic_tools import get_flat_topic_tree, video_dict_by_video_id, get_exercise_data, get_assessment_item_cache
from kalite.updates.api_views import annotate_topic_tree
from kalite.shared.api_auth import UserObjectsOnlyAuthorization
from kalite.facility.api_resources import FacilityUserResource


class ExerciseLogResource(ModelResource):

    user = fields.ForeignKey(FacilityUserResource, 'user')

    class Meta:
        queryset = ExerciseLog.objects.all()
        resource_name = 'exerciselog'
        filtering = {
            "exercise_id": ('exact', ),
            "user": ('exact', ),
        }
        authorization = UserObjectsOnlyAuthorization()


class AttemptLogResource(ModelResource):

    user = fields.ForeignKey(FacilityUserResource, 'user')

    class Meta:
        queryset = AttemptLog.objects.all().order_by("-timestamp")
        resource_name = 'attemptlog'
        filtering = {
            "exercise_id": ('exact', ),
            "user": ('exact', ),
            "context_type": ('exact', ),
        }
        authorization = UserObjectsOnlyAuthorization()


class Video:

    def __init__(self, lang_code="en", **kwargs):

        self.on_disk = False

        for k, v in kwargs.iteritems():
            setattr(self, k, v)

        # the computed values
        self.video_urls = kwargs.get('availability', {}).get(lang_code, {})
        self.subtitle_urls = kwargs.get('availability', {}).get(lang_code, {}).get('subtitles', {})
        self.selected_language = lang_code
        self.dubs_available = len(kwargs.get('availability', {})) > 1
        self.title = _(kwargs.get('title'))
        self.id = self.pk = self.video_id = kwargs.get('id')
        self.description = _(kwargs.get('description', ''))
        if self.description == "None":
            self.description = ""


class VideoResource(Resource):
    # TODO(jamalex): this seems very un-DRY (since it's replicating all the model fields again). DRY it out!
    availability = fields.DictField(attribute='availability')
    description = fields.CharField(attribute='description')
    download_urls = fields.DictField(attribute='download_urls')
    dubs_available = fields.BooleanField(attribute='dubs_available')
    duration = fields.IntegerField(attribute='duration')
    id = fields.CharField(attribute='id')
    kind = fields.CharField(attribute='kind')
    on_disk = fields.BooleanField(attribute='on_disk')
    path = fields.CharField(attribute='path')
    related_exercise = fields.DictField(attribute='related_exercise', default={})
    selected_language = fields.CharField(attribute='selected_language')
    subtitle_urls = fields.ListField(attribute='subtitle_urls')
    title = fields.CharField(attribute='title')
    video_id = fields.CharField(attribute='video_id')
    video_urls = fields.DictField(attribute='video_urls')
    youtube_id = fields.CharField(attribute='youtube_id')

    class Meta:
        resource_name = 'video'
        object_class = Video

    @staticmethod
    def _retrieve_id_from_path(video):
        # Note: same as _clean_playlist_entry_id in playlist/api_resources.py.
        # Unify both implementations!
        video = video.copy()
        path = video['path']
        # strip any trailing whitespace
        name = path.strip()

        # try to extract only the actual entity id
        name_breakdown = name.split('/')
        name_breakdown = [
            component for component
            in name.split('/')
            if component  # make sure component has something in it
        ]
        name = name_breakdown[-1]

        video['id'] = name
        return video

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}
        if isinstance(bundle_or_obj, Video):
            kwargs['pk'] = bundle_or_obj.id
        else:
            kwargs['pk'] = bundle_or_obj.obj.id

        return kwargs

    def get_object_list(self, request):
        topictree = get_flat_topic_tree(alldata=True)

        videos = [Video(**self._retrieve_id_from_path(videodict))
                  for videodict in topictree['Video'].itervalues()]

        return videos

    def obj_get_list(self, bundle, **kwargs):
        return self.get_object_list(bundle.request)

    def obj_get(self, bundle, **kwargs):
        topictree = get_flat_topic_tree(alldata=True)
        pk = kwargs['pk']
        videos_dict = video_dict_by_video_id(topictree)
        videodict = videos_dict.get(pk)

        if videodict:
            return Video(**self._retrieve_id_from_path(videodict))
        else:
            return None

    def obj_create(self, request):
        raise NotImplementedError

    def obj_update(self, bundle, **kwargs):
        raise NotImplementedError

    def obj_delete_list(self, request):
        raise NotImplementedError

    def obj_delete(self, request):
        raise NotImplementedError

    def rollback(self, request):
        raise NotImplementedError


class Exercise():

    def __init__(self, **kwargs):
        self.ancestor_ids = kwargs.get('ancestor_ids')
        self.lang = kwargs.get('lang')
        self.kind = kwargs.get('kind')
        self.all_assessment_items = kwargs.get('all_assessment_items')
        self.display_name = kwargs.get('display_name')
        self.description = kwargs.get('description')
        self.v_position = kwargs.get('v_position')
        self.title = kwargs.get('title')
        self.prerequisites = kwargs.get('prerequisites')
        self.name = kwargs.get('name')
        self.id = kwargs.get('id')
        self.seconds_per_fast_problem = kwargs.get('seconds_per_fast_problem')
        self.parent_id = kwargs.get('parent_id')
        self.template = kwargs.get('template')
        self.path = kwargs.get('path')
        self.h_position = kwargs.get('h_position')
        self.slug = kwargs.get('slug')
        self.exercise_id = kwargs.get('exercise_id')

class ExerciseResource(Resource):

    ancestor_ids = fields.CharField(attribute='ancestor_ids')
    lang = fields.CharField(attribute='lang', default='en')
    kind = fields.CharField(attribute='kind')
    all_assessment_items = fields.ListField(attribute='all_assessment_items')
    display_name = fields.CharField(attribute='display_name')
    description = fields.CharField(attribute='description')
    v_position = fields.IntegerField(attribute='v_position')
    title = fields.CharField(attribute='title')
    prerequisites = fields.ListField(attribute='prerequisites')
    name = fields.CharField(attribute='name')
    id = fields.CharField(attribute='id')
    seconds_per_fast_problem = fields.CharField(attribute='seconds_per_fast_problem')
    parent_id = fields.CharField(attribute='parent_id', null=True)
    template = fields.CharField(attribute='template')
    path = fields.CharField(attribute='path')
    h_position = fields.IntegerField(attribute='h_position')
    slug = fields.CharField(attribute='slug')
    exercise_id = fields.CharField(attribute='exercise_id')


    class Meta:
        resource_name = 'exercise'
        object_class = Exercise

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<id>[\w\d_.-]+)/$" % self._meta.resource_name,
                self.wrap_view('dispatch_detail'),
                name="api_dispatch_detail"),
        ]

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}
        if getattr(bundle_or_obj, 'obj', None):
            kwargs['pk'] = bundle_or_obj.obj.id
        else:
            kwargs['pk'] = bundle_or_obj.id
        return kwargs

    def obj_get_list(self, bundle, **kwargs):
        """
        Get the list of exercises based from a request.
        """
        raise NotImplemented("Operation not implemented yet for tests.")

    def obj_get(self, bundle, **kwargs):
        id = kwargs.get("id", None)
        exercise = get_exercise_data(bundle.request, id)
        if exercise:
            return Exercise(**exercise)
        else:
            raise NotFound('Exercise with id %s not found' % id)

    def obj_create(self, request):
        raise NotImplemented("Operation not implemented yet for exercises.")

    def obj_update(self, bundle, **kwargs):
        raise NotImplemented("Operation not implemented yet for exercises.")

    def obj_delete_list(self, request):
        raise NotImplemented("Operation not implemented yet for exercises.")

    def obj_delete(self, request):
        raise NotImplemented("Operation not implemented yet for exercises.")

    def rollback(self, request):
        raise NotImplemented("Operation not implemented yet for exercises.")


class AssessmentItem():

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.kind = kwargs.get('kind')
        self.name = kwargs.get('name')
        self.item_data = kwargs.get('item_data')
        self.tags = kwargs.get('tags')
        self.author_names = kwargs.get('author_names')
        self.sha = kwargs.get('sha')


class AssessmentItemResource(Resource):

    kind = fields.CharField(attribute='kind')
    name = fields.CharField(attribute='name')
    item_data = fields.CharField(attribute='item_data')
    tags = fields.CharField(attribute='tags')
    author_names = fields.CharField(attribute='author_names')
    sha = fields.CharField(attribute='sha')
    id = fields.CharField(attribute='id')


    class Meta:
        resource_name = 'assessment_item'
        object_class = AssessmentItem

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<id>[\w\d_.-]+)/$" % self._meta.resource_name,
                self.wrap_view('dispatch_detail'),
                name="api_dispatch_detail"),
        ]

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}
        if getattr(bundle_or_obj, 'obj', None):
            kwargs['pk'] = bundle_or_obj.obj.id
        else:
            kwargs['pk'] = bundle_or_obj.id
        return kwargs

    def obj_get_list(self, bundle, **kwargs):
        """
        Get the list of assessment_items based from a request.
        """
        raise NotImplemented("Operation not implemented yet for tests.")

    def obj_get(self, bundle, **kwargs):
        id = kwargs.get("id", None)
        assessment_item = get_assessment_item_cache().get(id, None)
        if assessment_item:
            return AssessmentItem(**assessment_item)
        else:
            raise NotFound('AssessmentItem with id %s not found' % id)

    def obj_create(self, request):
        raise NotImplemented("Operation not implemented yet for assessment_items.")

    def obj_update(self, bundle, **kwargs):
        raise NotImplemented("Operation not implemented yet for assessment_items.")

    def obj_delete_list(self, request):
        raise NotImplemented("Operation not implemented yet for assessment_items.")

    def obj_delete(self, request):
        raise NotImplemented("Operation not implemented yet for assessment_items.")

    def rollback(self, request):
        raise NotImplemented("Operation not implemented yet for assessment_items.")