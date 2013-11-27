from django.db import models

from datetime import datetime

from securesync.models import FacilityUser

from utils.django_utils import ExtendedModel

class ExperimentLog(ExtendedModel):

	minversion = "0.11"
	user = models.ForeignKey(FacilityUser, blank=False, null=False, db_index=True)
	activity_stage = models.IntegerField(blank=False, null=False, default=0)
	start_datetime = models.DateTimeField(blank=False, null=False, default=datetime.now)
	end_datetime = models.DateTimeField(blank=True, null=True)
	condition = models.IntegerField(blank=True, null=True)
	datacollect = models.CharField(max_length=200, blank=True, null=True)