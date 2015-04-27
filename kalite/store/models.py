import datetime

from django.db import models
from django.db.models import Sum
from django.dispatch import receiver
from django.core.exceptions import ValidationError

from kalite.student_testing.signals import exam_unset, unit_switch
from kalite.student_testing.models import TestLog
from kalite.student_testing.utils import get_current_unit_settings_value

from kalite.dynamic_assets.utils import load_dynamic_settings

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


@receiver(exam_unset, dispatch_uid="exam_unset")
def handle_exam_unset(sender, **kwargs):
    test_id = kwargs.get("test_id")
    if test_id:
        testlogs = TestLog.objects.filter(test=test_id)
        for testlog in testlogs:
            facility_user = testlog.user
            facility = facility_user.facility
            unit_id = get_current_unit_settings_value(facility.id)
            ds = load_dynamic_settings(user=facility_user)
            if ds["student_testing"].turn_on_points_for_practice_exams:
                transaction_log, created = StoreTransactionLog.objects.get_or_create(user=testlog.user, context_id=unit_id, context_type="output_condition", item="gift_card")
                try:
                    transaction_log.value = int(round(settings.UNIT_POINTS * float(testlog.total_correct)/testlog.total_number))
                except ZeroDivisionError:  # one of the students just hasn't started answering a test when we turn it off
                    continue
                transaction_log.save()


def playlist_group_mapping_reset_for_a_facility(facility_id):
    from kalite.playlist.models import PlaylistToGroupMapping
    from kalite.facility.models import FacilityGroup

    groups = FacilityGroup.objects.filter(facility=facility_id).values("id")
    playlist_group = PlaylistToGroupMapping.objects.all()
    for group in groups:
        for assigned_group in playlist_group:
            if assigned_group.group_id == group['id']:
                assigned_group.delete()

@receiver(unit_switch, dispatch_uid="unit_switch")
def handle_unit_switch(sender, **kwargs):
    old_unit = kwargs.get("old_unit")
    new_unit = kwargs.get("new_unit")
    facility_id = kwargs.get("facility_id")
    facility = Facility.objects.get(pk=facility_id)
    # Import here to avoid circular import
    from kalite.distributed.api_views import compute_total_points
    if old_unit != new_unit:
        if facility:
            users = FacilityUser.objects.filter(facility=facility_id)
            for user in users:
                old_unit_points = compute_total_points(user) or 0
                old_unit_transaction_log = StoreTransactionLog(user=user, context_id=old_unit, context_type="unit_points_reset", item="gift_card")
                old_unit_transaction_log.value = - old_unit_points
                old_unit_transaction_log.purchased_at = datetime.datetime.now()
                old_unit_transaction_log.save()
                new_unit_transaction_log = StoreTransactionLog.objects.filter(user=user, context_id=new_unit, context_type="unit_points_reset", item="gift_card")
                new_unit_transaction_log.soft_delete()

            playlist_group_mapping_reset_for_a_facility(facility_id)
