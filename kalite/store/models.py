from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.dispatch import receiver

from kalite.student_testing.signals import exam_unset
from kalite.student_testing.models import TestLog

from kalite.facility.models import FacilityUser

from securesync.models import DeferredCountSyncedModel

from django.conf import settings; logging = settings.LOG

# Create your models here.

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
            # TODO-BLOCKER (rtibbles): Dummy Store Item here - need to actually implement a gift card fixture
            item = StoreItem.objects.all()[0]
            transaction_log, created = StoreTransactionLog.objects.get_or_create(user=testlog.user, context_id=unit_id, context_type="output_condition", item=item)
            # TODO-BLOCKER (rtibbles): Needs setting of the overall points value for a unit
            overall_points_value_for_a_unit = 1000
            transaction_log.value = int(round(overall_points_value_for_a_unit*float(testlog.total_correct)/testlog.total_number))
            transaction_log.save()
            logging.debug(transaction_log.value)
