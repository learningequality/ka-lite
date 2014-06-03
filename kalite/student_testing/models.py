from django.db import models

from securesync.models import DeferredCountSyncedModel
from kalite.facility.models import FacilityUser

# class Test(ExtendedModel):
#   # ids is a JSON serialized list of ids that make up the test.
#   # Field max length set to 15000.
#   # This is greater than a concatenation of all the ids in the current KA exercises set.
#   ids = models.CharField(blank=False, null=False, max_length=15000)
#   # TODO: Field to tie Test to playlists that will be comparable across installations
#   repeats = models.IntegerField(blank=False, null=False, default=1)
#   seed = models.IntegerField(blank=False, null=False, default=1001)
#   title = models.CharField(blank=False, null=False, max_length=200)


class TestLog(DeferredCountSyncedModel):
    user = models.ForeignKey(FacilityUser, blank=False, null=False, db_index=True)
    # test = models.ForeignKey(Test, blank=False, null=False, db_index=True)
    test = models.CharField(blank=False, null=False, max_length=100)
    # TODO: Field that stores the Test/playlist field.
    index = models.IntegerField(blank=False, null=False, default=0)
    complete = models.BooleanField(blank=False, null=False, default=False)
    started = models.BooleanField(blank=False, null=False, default=False)
    total_number = models.IntegerField(blank=False, null=False, default=0)
    total_correct = models.IntegerField(blank=False, null=False, default=0)

    class Meta:  # needed to clear out the app_name property from SyncedClass.Meta
        pass