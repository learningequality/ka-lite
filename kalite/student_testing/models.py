from django.db import models

from fle_utils.django_utils import ExtendedModel
from kalite.facility.models import FacilityUser

from main.models import AttemptLog

class Test(ExtendedModel):
	path = models.CharField(blank=False, null=False, max_length=200)
	repeats = models.IntegerField(blank=False, null=False, default=0)
	seed = models.IntegerField(blank=False, null=False, default=1001)
	title = models.CharField(blank=False, null=False, max_length=200)

class TestLog(ExtendedModel):
	user = models.ForeignKey(FacilityUser, blank=False, null=False, db_index=True)
	test = models.ForeignKey(Test, blank=False, null=False, db_index=True)
	index = models.IntegerField(blank=False, null=False, default=0)
	repeat = models.IntegerField(blank=False, null=False, default=0)
	complete = models.BooleanField(blank=False, null=False, default=False)

class TestAttemptLog(AttemptLog):

	test_log = models.ForeignKey(TestLog, null=True)