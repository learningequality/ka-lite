from django.db import models
from django.utils.translation import ugettext_lazy as _

from kalite.facility.models import FacilityUser

from securesync.models import DeferredCountSyncedModel

# Create your models here.

class StoreTransactionLog(DeferredCountSyncedModel):
    """
    Model to track student 'expenditure' of points.
    """

    # TODO-BLOCKER(rtibbles): Update this to "0.13.0" (or whatever the release version number is at the time this goes upstream)

    minversion = "0.12.0"

    user = models.ForeignKey(FacilityUser, db_index=True)
    value = models.IntegerField(default=0)
    context_id = models.CharField(max_length=100, blank=True) # e.g. the unit id that it was spent/earned during
    context_type = models.CharField(max_length=100, blank=True)
    # can this transaction be undone by user actions? Initially set by 'returnable' on StoreItem, but can be changed subsequently
    reversible = models.BooleanField(default=False)
    item = models.ForeignKey(StoreItem, db_index=True)

    class Meta:  # needed to clear out the app_name property from SyncedClass.Meta
        pass


class StoreItem(DeferredCountSyncedModel):
    """
    Model to track items available for student purchase.
    """

    # TODO-BLOCKER(rtibbles): Update this to "0.13.0" (or whatever the release version number is at the time this goes upstream)

    minversion = "0.12.0"

    cost = models.IntegerField(default=0)
    returnable = models.BooleanField(default=False) # can this item be returned to the store for a refund?
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, verbose_name=_("Description"))
    thumbnail = models.TextField(blank=True) # data URI for image of item
    # Fields to map onto arbitrary resources like avatars, etc.
    resource_id = models.CharField(max_length=100, blank=True)
    resource_type = models.CharField(max_length=100, blank=True)

    class Meta:  # needed to clear out the app_name property from SyncedClass.Meta
        pass