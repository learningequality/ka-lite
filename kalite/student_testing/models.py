import glob
import json
import os

from django.db import models

from django.conf import settings
from django.core.urlresolvers import reverse

from securesync.models import DeferredCountSyncedModel
from kalite.facility.models import FacilityUser


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
