import random
import uuid
from annoying.functions import get_object_or_None
from math import ceil
from datetime import datetime
from dateutil import relativedelta

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

import i18n
import settings
from facility.models import FacilityUser
from securesync import engine
from securesync.models import DeferredCountSyncedModel, SyncedModel, Device
from settings import LOG as logging
from utils.django_utils import ExtendedModel
from utils.general import datediff, isnumeric


class VideoLog(DeferredCountSyncedModel):
    POINTS_PER_VIDEO = 750

    user = models.ForeignKey(FacilityUser, blank=True, null=True, db_index=True)
    video_id = models.CharField(max_length=100, db_index=True); video_id.minversion="0.10.3"
    youtube_id = models.CharField(max_length=20)
    total_seconds_watched = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    language = models.CharField(max_length=8, blank=True, null=True); language.minversion="0.10.3"
    complete = models.BooleanField(default=False)
    completion_timestamp = models.DateTimeField(blank=True, null=True)
    completion_counter = models.IntegerField(blank=True, null=True)

    class Meta:  # needed to clear out the app_name property from SyncedClass.Meta
        pass

    def __unicode__(self):
        return u"user=%s, video_id=%s, youtube_id=%s, seconds=%d, points=%d, language=%s%s" % (
            self.user,
            self.video_id,
            self.youtube_id,
            self.total_seconds_watched,
            self.points,
            self.language,
            " (completed)" if self.complete else "",
        )

    def save(self, update_userlog=True, *args, **kwargs):
        # To deal with backwards compatibility,
        #   check video_id, whether imported or not.
        if not self.video_id:
            assert kwargs.get("imported", False), "video_id better be set by internal code."
            assert self.youtube_id, "If not video_id, you better have set youtube_id!"
            self.video_id = i18n.get_video_id(self.youtube_id) or self.youtube_id  # for unknown videos, default to the youtube_id

        if not kwargs.get("imported", False):
            self.full_clean()

            # Compute learner status
            already_complete = self.complete
            self.complete = (self.points >= VideoLog.POINTS_PER_VIDEO)
            if not already_complete and self.complete:
                self.completion_timestamp = datetime.now()

            # Tell logins that they are still active (ignoring validation failures).
            #   TODO(bcipolli): Could log video information in the future.
            if update_userlog:
                try:
                    UserLog.update_user_activity(self.user, activity_type="login", update_datetime=(self.completion_timestamp or datetime.now()), language=self.language)
                except ValidationError as e:
                    logging.error("Failed to update userlog during video: %s" % e)

        super(VideoLog, self).save(*args, **kwargs)

    def get_uuid(self, *args, **kwargs):
        assert self.user is not None and self.user.id is not None, "User ID required for get_uuid"
        assert self.youtube_id is not None, "Youtube ID required for get_uuid"

        namespace = uuid.UUID(self.user.id)
        # can be video_id because that's set to the english youtube_id, to match past code.
        return uuid.uuid5(namespace, self.video_id.encode("utf-8")).hex


    @staticmethod
    def get_points_for_user(user):
        return VideoLog.objects.filter(user=user).aggregate(Sum("points")).get("points__sum", 0) or 0

    @classmethod
    def calc_points(cls, seconds_watched, video_length):
        return ceil(float(seconds_watched) / video_length* VideoLog.POINTS_PER_VIDEO)

    @classmethod
    def update_video_log(cls, facility_user, video_id, youtube_id, total_seconds_watched, language, points=0, new_points=0):
        assert facility_user and video_id and youtube_id, "Updating a video log requires a facility user, video ID, and a YouTube ID"

        # retrieve the previous video log for this user for this video, or make one if there isn't already one
        (videolog, _) = cls.get_or_initialize(user=facility_user, video_id=video_id)

        # combine the previously watched counts with the new counts
        #
        # Set total_seconds_watched directly, rather than incrementally, for robustness
        #   as sometimes an update request fails, and we'd miss the time update!
        videolog.total_seconds_watched = total_seconds_watched
        videolog.points = min(max(points, videolog.points + new_points), cls.POINTS_PER_VIDEO)
        videolog.language = language
        videolog.youtube_id = youtube_id

        # write the video log to the database, overwriting any old video log with the same ID
        # (and since the ID is computed from the user ID and YouTube ID, this will behave sanely)
        videolog.full_clean()
        videolog.save()

        return videolog


class ExerciseLog(DeferredCountSyncedModel):
    user = models.ForeignKey(FacilityUser, blank=True, null=True, db_index=True)
    exercise_id = models.CharField(max_length=100, db_index=True)
    streak_progress = models.IntegerField(default=0)
    attempts = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    language = models.CharField(max_length=8, blank=True, null=True); language.minversion="0.10.3"
    complete = models.BooleanField(default=False)
    struggling = models.BooleanField(default=False)
    attempts_before_completion = models.IntegerField(blank=True, null=True)
    completion_timestamp = models.DateTimeField(blank=True, null=True)
    completion_counter = models.IntegerField(blank=True, null=True)

    class Meta:  # needed to clear out the app_name property from SyncedClass.Meta
        pass

    def __unicode__(self):
        return u"user=%s, exercise_id=%s, points=%d, language=%s%s" % (self.user, self.exercise_id, self.points, self.language, " (completed)" if self.complete else "")

    def save(self, update_userlog=True, *args, **kwargs):
        if not kwargs.get("imported", False):
            self.full_clean()

            # Compute learner status
            if self.attempts > 20 and not self.complete:
                self.struggling = True
            already_complete = self.complete
            self.complete = (self.streak_progress >= 100)
            if not already_complete and self.complete:
                self.struggling = False
                self.completion_timestamp = datetime.now()
                self.attempts_before_completion = self.attempts

            # Tell logins that they are still active (ignoring validation failures).
            #   TODO(bcipolli): Could log exercise information in the future.
            if update_userlog:
                try:
                    UserLog.update_user_activity(self.user, activity_type="login", update_datetime=(self.completion_timestamp or datetime.now()), language=self.language)
                except ValidationError as e:
                    logging.error("Failed to update userlog during exercise: %s" % e)

        super(ExerciseLog, self).save(*args, **kwargs)

    def get_uuid(self, *args, **kwargs):
        assert self.user is not None and self.user.id is not None, "User ID required for get_uuid"
        assert self.exercise_id is not None, "Exercise ID required for get_uuid"

        namespace = uuid.UUID(self.user.id)
        return uuid.uuid5(namespace, self.exercise_id.encode("utf-8")).hex

    @classmethod
    def calc_points(cls, basepoints, ncorrect=1, add_randomness=True):
        # This is duplicated in javascript, in kalite/static/js/exercises.js
        inc = 0
        for i in range(ncorrect):
            bumpprob = 100 * random.random()
            # If we're adding randomness, then we add
            # 50% more points 9% of the time,
            # 100% more points 1% of the time.
            bump = 1.0 + add_randomness * (0.5*(bumpprob >= 90) + 0.5*(bumpprob>=99))
            inc += basepoints * bump;
        return ceil(inc)

    @staticmethod
    def get_points_for_user(user):
        return ExerciseLog.objects.filter(user=user).aggregate(Sum("points")).get("points__sum", 0) or 0


class UserLogSummary(DeferredCountSyncedModel):
    """Like UserLogs, but summarized over a longer period of time.
    Also sync'd across devices.  Unique per user, device, activity_type, and time period."""
    minversion = "0.9.4"

    device = models.ForeignKey(Device, blank=False, null=False)
    user = models.ForeignKey(FacilityUser, blank=False, null=False, db_index=True)
    activity_type = models.IntegerField(blank=False, null=False)
    language = models.CharField(max_length=8, blank=True, null=True)
    start_datetime = models.DateTimeField(blank=False, null=False)
    end_datetime = models.DateTimeField(blank=True, null=True)
    count = models.IntegerField(default=0, blank=False, null=False)
    total_seconds = models.IntegerField(default=0, blank=False, null=False)
    last_activity_datetime = models.DateTimeField(blank=True, null=True); last_activity_datetime.minversion = "0.10.3"

    class Meta:  # needed to clear out the app_name property from SyncedClass.Meta
        pass

    def __unicode__(self):
        self.full_clean()  # make sure everything that has to be there, is there.
        return u"%d seconds over %d logins for %s/%s/%d, period %s to %s" % (self.total_seconds, self.count, self.device.name, self.user.username, self.activity_type, self.start_datetime, self.end_datetime)

    @classmethod
    def get_period_start_datetime(cls, log_time, summary_freq):
        """Periods can be: days, weeks, months, years.
        Days referenced from midnight on the current computer's clock.
        Weeks referenced from Monday morning @ 00:00:00am.
        Months and years follow from the above."""

        summary_freq_qty    = summary_freq[0]
        summary_freq_period = summary_freq[1].lower()
        base_time = log_time.replace(microsecond=0, second=0, minute=0, hour=0)

        if summary_freq_period in ["day", "days"]:
            assert summary_freq_qty == 1, "Days only supports 1"
            return base_time

        elif summary_freq_period in ["week", "weeks"]:
            assert summary_freq_qty == 1, "Weeks only supports 1"
            raise NotImplementedError("Still working to implement weeks.")

        elif summary_freq_period in ["month", "months"]:
            assert summary_freq_qty in [1,2,3,4,6], "Months only supports [1,2,3,4,6]"
            # Integer math makes this equation work as desired
            return base_time.replace(day=1, month=log_time.month / summary_freq_qty * summary_freq_qty)

        elif summary_freq_period in ["year", "years"]:
            assert summary_freq_qty in [1,2,3,4,6], "Years only supports 1"
            return base_time.replace(day=1, month=1)

        else:
            raise NotImplementedError("Unrecognized summary frequency period: %s" % summary_freq_period)


    @classmethod
    def get_period_end_datetime(cls, log_time, summary_freq):
        start_datetime = cls.get_period_start_datetime(log_time, summary_freq)
        summary_freq_qty    = summary_freq[0]
        summary_freq_period = summary_freq[1].lower()

        if summary_freq_period in ["day", "days"]:
            return start_datetime + relativedelta.relativedelta(days=summary_freq_qty) - relativedelta.relativedelta(seconds=1)

        elif summary_freq_period in ["week", "weeks"]:
            return start_datetime + relativedelta.relativedelta(days=7*summary_freq_qty) - relativedelta.relativedelta(seconds=1)

        elif summary_freq_period in ["month", "months"]:
            return start_datetime + relativedelta.relativedelta(months=summary_freq_qty) - relativedelta.relativedelta(seconds=1)

        elif summary_freq_period in ["year", "years"]:
            return start_datetime + relativedelta.relativedelta(years=summary_freq_qty) - relativedelta.relativedelta(seconds=1)

        else:
            raise NotImplementedError("Unrecognized summary frequency period: %s" % summary_freq_period)


    @classmethod
    def add_log_to_summary(cls, user_log, device=None):
        """Adds total_time to the appropriate user/device/activity's summary log."""

        assert user_log.end_datetime, "all log items must have an end_datetime to be saved here."
        assert user_log.total_seconds >= 0, "all log items must have a non-negative total_seconds to be saved here."
        device = device or Device.get_own_device()  # Must be done here, or install fails

        # Check for an existing object
        log_summary = cls.objects.filter(
            device=device,
            user=user_log.user,
            activity_type=user_log.activity_type,
            start_datetime__lte=user_log.end_datetime,
            end_datetime__gte=user_log.end_datetime,
        )
        assert log_summary.count() <= 1, "There should never be multiple summaries in the same time period/device/user/type combo"

        # Get (or create) the log item
        log_summary = log_summary[0] if log_summary.count() else cls(
            device=device,
            user=user_log.user,
            activity_type=user_log.activity_type,
            language=user_log.language,
            start_datetime=cls.get_period_start_datetime(user_log.end_datetime, settings.USER_LOG_SUMMARY_FREQUENCY),
            end_datetime=cls.get_period_end_datetime(user_log.end_datetime, settings.USER_LOG_SUMMARY_FREQUENCY),
            total_seconds=0,
            count=0,
        )

        logging.debug("Adding %d seconds for %s/%s/%d/%s, period %s to %s" % (user_log.total_seconds, device.name, user_log.user.username, user_log.activity_type, user_log.language, log_summary.start_datetime, log_summary.end_datetime))

        # Add the latest info
        log_summary.total_seconds += user_log.total_seconds
        log_summary.count += 1
        log_summary.last_activity_datetime = user_log.last_active_datetime
        log_summary.save()


class UserLog(ExtendedModel):  # Not sync'd, only summaries are
    """Detailed instances of user behavior.
    Currently not sync'd (only used for local detail reports).
    """

    # Currently, all activity is used just to update logged-in-time.
    KNOWN_TYPES={"login": 1, "coachreport": 2}
    minversion = "0.9.4"

    user = models.ForeignKey(FacilityUser, blank=False, null=False, db_index=True)
    activity_type = models.IntegerField(blank=False, null=False)
    language = models.CharField(max_length=8, blank=True, null=True); language.minversion="0.10.3"
    start_datetime = models.DateTimeField(blank=False, null=False)
    last_active_datetime = models.DateTimeField(blank=False, null=False)
    end_datetime = models.DateTimeField(blank=True, null=True)
    total_seconds = models.IntegerField(blank=True, null=True)

    @staticmethod
    def is_enabled():
        return settings.USER_LOG_MAX_RECORDS_PER_USER != 0

    def __unicode__(self):
        if self.end_datetime:
            return u"%s (%s): logged in @ %s; for %s seconds" % (self.user.username, self.language, self.start_datetime, self.total_seconds)
        else:
            return u"%s (%s): logged in @ %s; last active @ %s" % (self.user.username, self.language, self.start_datetime, self.last_active_datetime)

    def save(self, *args, **kwargs):
        """When this model is saved, check if the activity is ended.
        If so, compute total_seconds and update the corresponding summary log."""

        # Do nothing if the max # of records is zero
        # (i.e. this functionality is disabled)
        if not self.is_enabled():
            return

        # Setting up data consistency now falls into the pre-save listener.
        # Culling of records will be done as a post-save listener.
        super(UserLog, self).save(*args, **kwargs)

    @classmethod
    def get_activity_int(cls, activity_type):
        """Helper function converts from string or int to the underlying int"""

        if type(activity_type).__name__ in ["str", "unicode"]:
            if activity_type in cls.KNOWN_TYPES:
                return cls.KNOWN_TYPES[activity_type]
            else:
                raise Exception("Unrecognized activity type: %s" % activity_type)

        elif isnumeric(activity_type):
            return int(activity_type)

        else:
            raise Exception("Cannot convert requested activity_type to int")

    @classmethod
    def get_latest_open_log_or_None(cls, *args, **kwargs):
        assert not args
        assert "end_datetime" not in kwargs

        logs = cls.objects \
            .filter(end_datetime__isnull=True, **kwargs) \
            .order_by("-last_active_datetime")
        return None if not logs else logs[0]

    @classmethod
    def begin_user_activity(cls, user, activity_type="login", start_datetime=None, language=None, suppress_save=False):
        """Helper function to create a user activity log entry."""

        # Do nothing if the max # of records is zero
        # (i.e. this functionality is disabled)
        if not cls.is_enabled():
            return

        if not user:
            raise ValidationError("A valid user must always be specified.")
        if not start_datetime:  # must be done outside the function header (else becomes static)
            start_datetime = datetime.now()
        activity_type = cls.get_activity_int(activity_type)

        cur_log = cls.get_latest_open_log_or_None(user=user, activity_type=activity_type)
        if cur_log:
            # Seems we're logging in without logging out of the previous.
            #   Best thing to do is simulate a login
            #   at the previous last update time.
            #
            # Note: this can be a recursive call
            logging.warn("%s: had to END activity on a begin(%d) @ %s" % (user.username, activity_type, start_datetime))
            # Don't mark current language when closing an old one
            cls.end_user_activity(user=user, activity_type=activity_type, end_datetime=cur_log.last_active_datetime)  # can't suppress save
            cur_log = None

        # Create a new entry
        logging.debug("%s: BEGIN activity(%d) @ %s" % (user.username, activity_type, start_datetime))
        cur_log = cls(user=user, activity_type=activity_type, start_datetime=start_datetime, last_active_datetime=start_datetime, language=language)
        if not suppress_save:
            cur_log.save()

        return cur_log

    @classmethod
    def update_user_activity(cls, user, activity_type="login", update_datetime=None, language=None, suppress_save=False):
        """Helper function to update an existing user activity log entry."""

        # Do nothing if the max # of records is zero
        # (i.e. this functionality is disabled)
        if not cls.is_enabled():
            return

        if not user:
            raise ValidationError("A valid user must always be specified.")
        if not update_datetime:  # must be done outside the function header (else becomes static)
            update_datetime = datetime.now()
        activity_type = cls.get_activity_int(activity_type)

        cur_log = cls.get_latest_open_log_or_None(user=user, activity_type=activity_type)
        if cur_log:
            # How could you start after you updated??
            if cur_log.start_datetime > update_datetime:
                raise ValidationError("Update time must always be later than the login time.")
        else:
            # No unstopped starts.  Start should have been called first!
            logging.warn("%s: Had to create a user log entry on an UPDATE(%d)! @ %s" % (user.username, activity_type, update_datetime))
            cur_log = cls.begin_user_activity(user=user, activity_type=activity_type, start_datetime=update_datetime, suppress_save=True)

        logging.debug("%s: UPDATE activity (%d) @ %s" % (user.username, activity_type, update_datetime))
        cur_log.last_active_datetime = update_datetime
        cur_log.language = language or cur_log.language  # set the language to the current language, if there is one.
        if not suppress_save:
            cur_log.save()
        return cur_log

    @classmethod
    def end_user_activity(cls, user, activity_type="login", end_datetime=None, suppress_save=False):  # don't accept language--we're just closing previous activity.
        """Helper function to complete an existing user activity log entry."""

        # Do nothing if the max # of records is zero
        # (i.e. this functionality is disabled)
        if not cls.is_enabled():
            return

        if not user:
            raise ValidationError("A valid user must always be specified.")
        if not end_datetime:  # must be done outside the function header (else becomes static)
            end_datetime = datetime.now()
        activity_type = cls.get_activity_int(activity_type)

        cur_log = cls.get_latest_open_log_or_None(user=user, activity_type=activity_type)

        if cur_log:
            # How could you start after you ended??
            if cur_log.start_datetime > end_datetime:
                raise ValidationError("Update time must always be later than the login time.")
        else:
            # No unstopped starts.  Start should have been called first!
            logging.warn("%s: Had to BEGIN a user log entry, but ENDING(%d)! @ %s" % (user.username, activity_type, end_datetime))
            cur_log = cls.begin_user_activity(user=user, activity_type=activity_type, start_datetime=end_datetime, suppress_save=True)

        logging.debug("%s: Logging LOGOUT activity @ %s" % (user.username, end_datetime))
        cur_log.end_datetime = end_datetime
        if not suppress_save:
            cur_log.save()  # total-seconds will be computed here.
        return cur_log

@receiver(pre_save, sender=UserLog)
def add_to_summary(sender, **kwargs):
    assert UserLog.is_enabled(), "We shouldn't be saving unless UserLog is enabled."

    instance = kwargs["instance"]

    if not instance.start_datetime:
        raise ValidationError("start_datetime cannot be None")
    if instance.last_active_datetime and instance.start_datetime > instance.last_active_datetime:
        raise ValidationError("UserLog date consistency check for start_datetime and last_active_datetime")

    if instance.end_datetime and not instance.total_seconds:
        # Compute total_seconds, save to summary
        #   Note: only supports setting end_datetime once!
        instance.full_clean()

        # The top computation is more lenient: user activity is just time logged in, literally.
        # The bottom computation is more strict: user activity is from start until the last "action"
        #   recorded--in the current case, that means from login until the last moment an exercise or
        #   video log was updated.
        #instance.total_seconds = datediff(instance.end_datetime, instance.start_datetime, units="seconds")
        instance.total_seconds = 0 if not instance.last_active_datetime else datediff(instance.last_active_datetime, instance.start_datetime, units="seconds")

        # Confirm the result (output info first for easier debugging)
        if instance.total_seconds < 0:
            raise ValidationError("Total learning time should always be non-negative.")
        logging.debug("%s: total time (%d): %d seconds" % (instance.user.username, instance.activity_type, instance.total_seconds))

        # Save only completed log items to the UserLogSummary
        UserLogSummary.add_log_to_summary(instance)

@receiver(post_save, sender=UserLog)
def cull_records(sender, **kwargs):
    """
    Listen in to see when videos become available.
    """
    if settings.USER_LOG_MAX_RECORDS_PER_USER and kwargs["created"]:  # Works for None, out of the box
        current_models = UserLog.objects.filter(user=kwargs["instance"].user, activity_type=kwargs["instance"].activity_type)
        if current_models.count() > settings.USER_LOG_MAX_RECORDS_PER_USER:
            # Unfortunately, could not do an aggregate delete when doing a
            #   slice in query
            to_discard = current_models \
                .order_by("start_datetime")[0:current_models.count() - settings.USER_LOG_MAX_RECORDS_PER_USER]
            UserLog.objects.filter(pk__in=to_discard).delete()


engine.add_syncing_models([VideoLog, ExerciseLog, UserLogSummary])
