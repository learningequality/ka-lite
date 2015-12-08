import datetime

from django.db import models
from django.db.models import Sum
from django.dispatch import receiver
from django.core.exceptions import ValidationError

from kalite.facility.models import FacilityUser, Facility

from securesync.models import DeferredCountSyncedModel

from django.conf import settings; logging = settings.LOG

class StoreTransactionLog(DeferredCountSyncedModel):
    """
    Model to track student 'expenditure' of points.
    """

    # TODO(rtibbles): Update this to "0.13.0" (or whatever the release version number is at the time this goes upstream)

    minversion = "0.13.0"

    user = models.ForeignKey(FacilityUser, db_index=True)
    value = models.IntegerField(default=0)
    context_id = models.CharField(max_length=100, blank=True) # e.g. the unit id that it was spent/earned during
    context_type = models.CharField(max_length=100, blank=True)
    # can this transaction be undone by user actions? Initially set by 'returnable' on StoreItem, but can be changed subsequently
    reversible = models.BooleanField(default=False)
    item = models.CharField(max_length=100, db_index=True)
    purchased_at = models.DateTimeField(blank=True, null=True)

    class Meta:  # needed to clear out the app_name property from SyncedClass.Meta
        pass
