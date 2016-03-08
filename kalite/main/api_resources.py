from tastypie import fields
from tastypie.resources import ModelResource

from .models import VideoLog, ExerciseLog, AttemptLog, ContentLog, ContentRating

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
        ordering = [
            "timestamp",
        ]
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


class ContentRatingResource(ModelResource):

    user = fields.ForeignKey(FacilityUserResource, 'user')

    class Meta:
        resource_name = 'content_rating'
        queryset = ContentRating.objects.all()
        filtering = {
            "content_id": ('exact', 'in', ),
            "content_kind": ('exact', 'in', ),
            "user": ('exact', ),
        }
        authorization = UserObjectsOnlyAuthorization()
