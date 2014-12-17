from tastypie import fields
from tastypie.resources import ModelResource, Resource

from django.utils.translation import ugettext as _

from .models import ExerciseLog, AttemptLog

from kalite.topic_tools import get_flat_topic_tree, video_dict_by_video_id
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
            "context_type": ('exact', 'in', ),
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
