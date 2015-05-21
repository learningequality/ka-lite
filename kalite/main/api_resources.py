import json
from tastypie import fields
from tastypie.resources import ModelResource, Resource
from tastypie.exceptions import NotFound
from django.conf.urls import url
from django.conf import settings

from .models import VideoLog, ExerciseLog, AttemptLog, ContentLog, AssessmentItem

from kalite.distributed.api_views import get_messages_for_api_calls
from kalite.topic_tools import get_exercise_data, get_assessment_item_data, get_content_data
from kalite.topic_tools.content_recommendation import get_resume_recommendations, get_next_recommendations, get_explore_recommendations
from kalite.shared.api_auth.auth import UserObjectsOnlyAuthorization
from kalite.facility.api_resources import FacilityUserResource


class ExerciseLogResource(ModelResource):

    user = fields.ForeignKey(FacilityUserResource, 'user')

    class Meta:
        queryset = ExerciseLog.objects.all()
        resource_name = 'exerciselog'
        filtering = {
            "exercise_id": ('exact', 'in', ),
            "user": ('exact', ),
        }
        authorization = UserObjectsOnlyAuthorization()

    def obj_create(self, bundle, **kwargs):
        is_admin = getattr(bundle.request, "is_admin", False)
        user = getattr(bundle.request, "user", None)
        if is_admin:
            if user and getattr(user, 'is_superuser', False):
                return None
        return super(ExerciseLogResource, self).obj_create(bundle, **kwargs)


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

    def obj_create(self, bundle, **kwargs):
        is_admin = getattr(bundle.request, "is_admin", False)
        user = getattr(bundle.request, "user", None)
        if is_admin:
            if user and getattr(user, 'is_superuser', False):
                return None
        return super(AttemptLogResource, self).obj_create(bundle, **kwargs)


class ContentLogResource(ModelResource):

    user = fields.ForeignKey(FacilityUserResource, 'user')

    class Meta:
        queryset = ContentLog.objects.all()
        resource_name = 'contentlog'
        filtering = {
            "content_id": ('exact', 'in', ),
            "user": ('exact', ),
        }
        authorization = UserObjectsOnlyAuthorization()


class VideoLogResource(ModelResource):

    user = fields.ForeignKey(FacilityUserResource, 'user')

    class Meta:
        queryset = VideoLog.objects.all()
        resource_name = 'videolog'
        filtering = {
            "video_id": ('exact', 'in', ),
            "user": ('exact', ),
        }
        authorization = UserObjectsOnlyAuthorization()


class Exercise():

    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)


class ExerciseResource(Resource):
    lang = fields.CharField(attribute='lang', default='en')
    kind = fields.CharField(attribute='kind')
    all_assessment_items = fields.ListField(attribute='all_assessment_items', default=[])
    display_name = fields.CharField(attribute='display_name')
    description = fields.CharField(attribute='description')
    title = fields.CharField(attribute='title')
    prerequisites = fields.ListField(attribute='prerequisites')
    name = fields.CharField(attribute='name')
    id = fields.CharField(attribute='id')
    seconds_per_fast_problem = fields.CharField(attribute='seconds_per_fast_problem')
    basepoints = fields.CharField(attribute='basepoints', default='10')
    template = fields.CharField(attribute='template')
    path = fields.CharField(attribute='path')
    slug = fields.CharField(attribute='slug')
    exercise_id = fields.CharField(attribute='exercise_id')
    uses_assessment_items = fields.BooleanField(attribute='uses_assessment_items')
    available = fields.BooleanField(attribute='available', default=True)

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
        Get the list of exercises.
        """
        raise NotImplemented("Operation not implemented yet for videos.")

    def obj_get(self, bundle, **kwargs):
        id = kwargs.get("id", None)
        exercise = get_exercise_data(bundle.request, id)
        if exercise:
            return Exercise(**exercise)
        else:
            raise NotFound('Exercise with id %s not found' % id)

    def obj_create(self, bundle, **kwargs):
        raise NotImplemented("Operation not implemented yet for exercises.")

    def obj_update(self, bundle, **kwargs):
        raise NotImplemented("Operation not implemented yet for exercises.")

    def obj_delete_list(self, bundle, **kwargs):
        raise NotImplemented("Operation not implemented yet for exercises.")

    def obj_delete(self, bundle, **kwargs):
        raise NotImplemented("Operation not implemented yet for exercises.")

    def rollback(self, bundles):
        raise NotImplemented("Operation not implemented yet for exercises.")


class AssessmentItemResource(ModelResource):
    class Meta:
        resource_name = 'assessment_item'
        queryset = AssessmentItem.objects.all()

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


    def obj_create(self, bundle, **kwargs):
        raise NotImplemented("Operation not implemented yet for assessment_items.")

    def obj_update(self, bundle, **kwargs):
        raise NotImplemented("Operation not implemented yet for assessment_items.")

    def obj_delete_list(self, bundle, **kwargs):
        raise NotImplemented("Operation not implemented yet for assessment_items.")

    def obj_delete(self, bundle, **kwargs):
        raise NotImplemented("Operation not implemented yet for assessment_items.")

    def rollback(self, bundles):
        raise NotImplemented("Operation not implemented yet for assessment_items.")


class Content:

    def __init__(self, lang_code="en", **kwargs):

        standard_fields = [
            "title",
            "description",
            "id",
            "author_name",
            "kind",
            "content_urls",
            "selected_language",
            "available",
        ]

        for k in standard_fields:
            setattr(self, k, kwargs.pop(k, ""))

        extra_fields = {}

        for k, v in kwargs.iteritems():
            extra_fields[k] = v

        # the computed values
        self.extra_fields = json.dumps(extra_fields)
        # TODO(MCGallaspy) This is inappropriate if multiple channels are active at once,
        # TODO(MCGallaspy) but given that there's only one active channel for 0.13 initially (khan)
        # TODO(MCGallaspy) I guess it's okay. In a multiple available channel situation then we should
        # TODO(MCGallaspy) probably get the source attribute from the content data itself.
        self.source = kwargs.pop("source", settings.CHANNEL)


class ContentResource(Resource):
    content_urls = fields.DictField(attribute='content_urls')
    description = fields.CharField(attribute='description', default="")
    id = fields.CharField(attribute='id')
    kind = fields.CharField(attribute='kind')
    available = fields.BooleanField(attribute='available')
    selected_language = fields.CharField(attribute='selected_language')
    title = fields.CharField(attribute='title')
    extra_fields = fields.CharField(attribute='extra_fields')
    source = fields.CharField(attribute='source')

    class Meta:
        resource_name = 'content'
        object_class = Content

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

    def get_object_list(self, request):
        """
        Get the list of content.
        """
        raise NotImplemented("Operation not implemented yet for content.")

    def obj_get_list(self, bundle, **kwargs):
        return self.get_object_list(bundle.request)

    def obj_get(self, bundle, **kwargs):
        content_id = kwargs.get("id", None)
        content = get_content_data(bundle.request, content_id)
        # MUST: Include messages in the api call.
        if content:
            content['messages'] = get_messages_for_api_calls(bundle.request)
            return Content(**content)
        else:
            raise NotFound('Content with id %s not found' % content_id)

    def obj_create(self, bundle, **kwargs):
        raise NotImplementedError

    def obj_update(self, bundle, **kwargs):
        raise NotImplementedError

    def obj_delete_list(self, bundle, **kwargs):
        raise NotImplementedError

    def obj_delete(self, bundle, **kwargs):
        raise NotImplementedError

    def rollback(self, bundles):
        raise NotImplementedError


class ContentRecommender(object):
    """
    Convert dictionary to object
    Adapted from @source http://stackoverflow.com/a/1305561/383912
    """
    def __init__(self, d=None):
        self.__dict__['d'] = d
 
    def __getattr__(self, key):
        value = ''

        try:
            value = self.__dict__['d'][key]
        except:
            pass

        if type(value) == type({}):
            return ContentRecommender(value)
 
        return value


class ContentRecommenderResource(Resource):
    # Define common fields to resume, next_steps, and explore
    next_steps = fields.BooleanField(attribute='next_steps', default=False)
    resume = fields.BooleanField(attribute='resume', default=False)
    explore = fields.BooleanField(attribute='explore', default=False)
    kind = fields.CharField(attribute='kind', null=True, blank=True)
    
    # Addition fields for resume and next_steps
    id = fields.CharField(attribute='id', null=True, blank=True)
    subtopic_title = fields.CharField(attribute='subtopic_title', null=True, blank=True)
    
    # Additional fields for resume recommendation(s) only
    title = fields.CharField(attribute='title', null=True, blank=True)
    youtube_id = fields.CharField(attribute='youtube_id', null=True, blank=True)
    
    # Additional fields for next_steps
    subtopic_id = fields.CharField(attribute='subtopic_id', null=True, blank=True)
    lesson_title = fields.CharField(attribute='lesson_title', null=True, blank=True)

    # Additional fields for explore reccommendations only
    accessed_subtopic = fields.CharField(attribute='accessed_subtopic', null=True, blank=True)
    suggested_subtopic_title = fields.CharField(attribute='suggested_subtopic_title', null=True, blank=True)
    suggested_subtopic_id = fields.CharField(attribute='suggested_subtopic_id', null=True, blank=True)
    
 
    class Meta:
        resource_name = 'contentrecommender'
        object_class = ContentRecommender
        authorization = UserObjectsOnlyAuthorization()
        filtering = {
            "user": ('exact', ),
        }

    def dehydrate(self, bundle):
        """Remove unused fields...resume, next_steps, and explore have different fields."""
        field_names = [x for x in bundle.data]

        for field_name in field_names:
            if not bundle.data[field_name]:
                del bundle.data[field_name]

        return bundle

    def get_object_list(self, request):
        """Populate response with recommendation(s)"""
        user = getattr(request, "user", None)
        recommendations = []
        
        # TODO: check if multiple filters exist
        # filters = request.GET.get('filters', None)

        # retrieve resume recommendation(s) and set resume boolean flag
        resume_recommendations = get_resume_recommendations(user)
        for item in resume_recommendations:
            item['resume'] = True
            recommendations.append(ContentRecommender(item))

        # retrieve next_steps recommendations, set next_steps boolean flag, and flatten results for api response
        next_recommendations = get_next_recommendations(user)
        for item in next_recommendations:
            temp = {}
            temp['next_steps'] = True
            temp['id'] = item.keys()[0]
            temp['kind'] = item[temp['id']]['kind']
            temp['subtopic_title'] = item[temp['id']]['subtopic_title']
            temp['subtopic_id'] = item[temp['id']]['subtopic_id']
            temp['lesson_title'] = item[temp['id']]['lesson_title']

            recommendations.append(ContentRecommender(temp))

        # retrieve explore recommendations, set explore boolean flag, and flatten results for api response
        explore_recommendations = get_explore_recommendations(user)
        for item in explore_recommendations:
            temp = {}
            temp['explore'] = True
            temp['kind'] = 'subtopic'
            temp['accessed_subtopic'] = item['accessed']
            
            # unpack each recommended subtopic and return each as separate recommendation
            for recommended_topic in item['recommended_topics']:
                temp['suggested_subtopic_title'] = recommended_topic['title']
                temp['suggested_subtopic_id'] = recommended_topic['id']
            
                recommendations.append(ContentRecommender(temp))

        return recommendations

    def obj_get_list(self, bundle, **kwargs):
        return self.get_object_list(bundle.request)

    def obj_get(self, bundle, **kwargs):
        raise NotImplemented("ContentRecommender is a collection resource.")

    def obj_create(self, bundle, **kwargs):
        raise NotImplemented("ContentRecommender is a read-only resource.")

    def obj_update(self, bundle, **kwargs):
        raise NotImplemented("ContentRecommender is a read-only resource.")

    def obj_delete_list(self, bundle, **kwargs):
        raise NotImplemented("ContentRecommender is a read-only resource.")

    def obj_delete(self, bundle, **kwargs):
        raise NotImplemented("ContentRecommender is a read-only resource.")

    def rollback(self, bundles):
        raise NotImplemented("ContentRecommender is a read-only resource.")
