import uuid

from django.conf import settings
from django.db import models

from kalite.facility.models import FacilityUser
from kalite.topic_tools.settings import CHANNEL

from securesync.models import DeferredCountSyncedModel

class ContentRating(DeferredCountSyncedModel):

    minversion = "0.15.0"

    class Meta:
        unique_together = ("content_source", "content_kind", "content_id", "user")

    # Maintain info on content type -- could be video, exercise, etc, but we should be able to uniquely id it
    content_kind = models.CharField(max_length=100, db_index=True, blank=False)
    content_id = models.CharField(max_length=100, db_index=True, blank=False)
    content_source = models.CharField(max_length=100, db_index=True, default=CHANNEL)

    user = models.ForeignKey(FacilityUser, blank=False)
    quality = models.IntegerField(blank=False, default=0)
    difficulty = models.IntegerField(blank=False, default=0)
    text = models.TextField(blank=True)

    def get_uuid(self):
        assert self.user is not None and self.user.id is not None, "User ID required for get_uuid"
        assert self.content_id is not None, "Content id required for get_uuid"
        assert self.content_kind is not None, "Content kind required for get_uuid"
        assert self.content_source is not None, "Content source required for get_uuid"

        namespace = uuid.UUID(self.user.id)
        hashtext = ":".join([self.__class__.__name__, self.content_source, self.content_kind, self.content_id])
        return uuid.uuid5(namespace, hashtext.encode("utf-8")).hex