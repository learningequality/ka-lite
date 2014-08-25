from django.db import models
from django.db.models import Sum
from django.utils.translation import ugettext_lazy as _
from django.dispatch import receiver
from django.core.exceptions import ValidationError

from kalite.student_testing.signals import exam_unset
from kalite.student_testing.models import TestLog
from kalite.student_testing.utils import get_current_unit_settings_value

from kalite.facility.models import FacilityUser

from securesync.models import DeferredCountSyncedModel

from django.conf import settings; logging = settings.LOG

from .data.items import STORE_ITEMS

# Create your models here.

# class StoreItem(DeferredCountSyncedModel):
#     """
#     Model to track items available for student purchase.
#     """

#     # TODO-BLOCKER(rtibbles): Update this to "0.13.0" (or whatever the release version number is at the time this goes upstream)

#     minversion = "0.12.0"

#     cost = models.IntegerField(default=0)
#     returnable = models.BooleanField(default=False) # can this item be returned to the store for a refund?
#     title = models.CharField(max_length=100)
#     description = models.TextField(blank=True, verbose_name=_("Description"))
#     thumbnail = models.TextField(blank=True) # data URI for image of item
#     # Fields to map onto arbitrary resources like avatars, etc.
#     resource_id = models.CharField(max_length=100, blank=True)
#     resource_type = models.CharField(max_length=100, blank=True)

#     class Meta:  # needed to clear out the app_name property from SyncedClass.Meta
#         pass

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

    minversion = "0.12.0"

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

    @staticmethod
    def get_points_for_user(user):
        return StoreTransactionLog.objects.filter(user=user).aggregate(Sum("value")).get("value__sum", 0) or 0

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


@receiver(exam_unset)
def handle_exam_unset(sender, **kwargs):
    test_id = kwargs.get("test_id")
    if test_id:
        # TODO (rtibbles): Add logic here to update or create a transaction for the test_id for all FacilityUsers that credits them with their points, but only if in the output condition
        logging.debug(test_id)
        testlogs = TestLog.objects.filter(test=test_id)
        for testlog in testlogs:
            # TODO-BLOCKER (rtibbles): Needs implementaton of unit_id settings module.
            unit_id = "things and stuff for testing"
            transaction_log, created = StoreTransactionLog.objects.get_or_create(user=testlog.user, context_id=unit_id, context_type="output_condition", item="gift_card")
            # TODO-BLOCKER (rtibbles): Needs setting of the overall points value for a unit
            overall_points_value_for_a_unit = 1000
            transaction_log.value = int(round(overall_points_value_for_a_unit*float(testlog.total_correct)/testlog.total_number))
            transaction_log.save()
            logging.debug(transaction_log.value)
