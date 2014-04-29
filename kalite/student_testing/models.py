from django.db import models

from fle_utils.django_utils import ExtendedModel
from kalite.facility.models import FacilityUser

from main.models import AttemptLog

class Test(ExtendedModel):
	# ids is a JSON serialized list of ids that make up the test.
	# Field max length set to 15000.
	# This is greater than a concatenation of all the ids in the current KA exercises set.
	ids = models.CharField(blank=False, null=False, max_length=15000)
	# TODO: Field to tie Test to playlists that will be comparable across installations
	repeats = models.IntegerField(blank=False, null=False, default=1)
	seed = models.IntegerField(blank=False, null=False, default=1001)
	title = models.CharField(blank=False, null=False, max_length=200)

class TestLog(ExtendedModel):
	user = models.ForeignKey(FacilityUser, blank=False, null=False, db_index=True)
	test = models.ForeignKey(Test, blank=False, null=False, db_index=True)
	# TODO: Field that stores the Test/playlist field.
	index = models.IntegerField(blank=False, null=False, default=0)
	# test_sequence is a JSON serialized list of tuples (id, seed) that define the order of the test.
	test_sequence = models.CharField(blank=True, null=True, max_length=30000)
	complete = models.BooleanField(blank=False, null=False, default=False)

class TestAttemptLog(AttemptLog):

	test_log = models.ForeignKey(TestLog, null=True)