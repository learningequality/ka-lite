import datetime

from django.db import models
from django.core.exceptions import ValidationError

from kalite.facility.models import FacilityUser, Facility

from securesync.models import DeferredCountSyncedModel

from django.conf import settings; logging = settings.LOG

from .data.items import STORE_ITEMS


class StoreItem():

    storeitemcache = {}

    def __init__(self, **kwargs):
        storeitem_id = kwargs.get('storeitem_id')
        self.storeitem_id = storeitem_id
        self.cost = kwargs.get("cost", None)
        self.returnable = kwargs.get("returnable", None)
        self.title = kwargs.get("title", None)
        self.description = kwargs.get("description", None)
        self.thumbnail = kwargs.get("thumbnail", None)
        self.resource_id = kwargs.get("resource_id", None)
        self.resource_type = kwargs.get("resource_type", None)
        self.shown = kwargs.get("shown", True)

    @classmethod
    def all(cls, force=False):
        if not cls.storeitemcache or force:
            for key, value in STORE_ITEMS.items():
                # Coerce each storeitem dict into a StoreItem object
                value["storeitem_id"] = key
                cls.storeitemcache[key] = (StoreItem(**value))
        return cls.storeitemcache


class StoreTransactionLog(DeferredCountSyncedModel):
    """
    Model to track student 'expenditure' of points.
    """

    # TODO-BLOCKER(rtibbles): Update this to "0.13.0" (or whatever the release version number is at the time this goes upstream)

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

    def save(self, *args, **kwargs):
        if not kwargs.get("imported", False):
            self.full_clean()
            storeitem_id = self.item
            if storeitem_id:
                item = StoreItem.all().get(storeitem_id, None)
                if not item:
                    # TODO (rtibbles): Cleanup! Hackity hack to deal with not using tastypie resource URI for item id.
                    storeitem_id = storeitem_id.split("/")[-2]
            item = StoreItem.all().get(storeitem_id, None)
            if not item:
                raise ValidationError("Store Item does not exist" + storeitem_id)
            elif item.cost:
                if item.cost != -self.value:
                    raise ValidationError("Store Item cost different from transaction_log value")

        super(StoreTransactionLog, self).save(*args, **kwargs)