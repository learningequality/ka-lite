from django.db import models

from fle_utils.django_utils import ExtendedModel

from kalite.facility.models import FacilityUser

# Create your models here.

class Playlist(ExtendedModel):
    title = models.CharField(max_length=30)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(FacilityUser, blank=True, null=True)

    def __unicode__(self):
        return "%(title)s:%(desc)s" % {'title': self.title, 'desc': self.description}


class PlaylistEntry(ExtendedModel):
    ENTITY_KINDS = (
        ('video', 'Video'),
        ('exercise', 'Exercise'),
        ('quiz', 'Quiz'),
    )

    entity_kind = models.CharField(max_length=10, choices=ENTITY_KINDS)
    entity_id = models.CharField(max_length=50)
    playlist = models.ForeignKey(Playlist)
    sort_order = models.IntegerField()
