from django.db import models

from utils.django_utils import ExtendedModel

class Experiment(ExtendedModel):

	minversion = "0.9.4"

    user = models.ForeignKey(FacilityUser, blank=False, null=False, db_index=True)
    activity_stage = models.IntegerField(blank=False, null=False)
    start_datetime = models.DateTimeField(blank=False, null=False)
    end_datetime = models.DateTimeField(blank=True, null=True)

    