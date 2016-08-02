"""
All models associated with user learning / usage, including:
* Exercise/Video progress
* Login stats
"""
import random
import uuid
from math import ceil
from datetime import datetime
from dateutil import relativedelta

from django.conf import settings; logging = settings.LOG
from django.contrib.auth.signals import user_logged_out
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from fle_utils.django_utils.classes import ExtendedModel
from fle_utils.general import datediff, isnumeric
from kalite.topic_tools.content_models import get_video_from_youtube_id
from kalite.facility.models import FacilityUser
from kalite.dynamic_assets.utils import load_dynamic_settings
from securesync.models import DeferredCountSyncedModel, Device
from kalite.topic_tools.settings import CHANNEL

from .content_rating_models import ContentRating


class VideoLog(DeferredCountSyncedModel):

    user = models.ForeignKey(FacilityUser, blank=True, null=True, db_index=True)
    video_id = models.CharField(max_length=200, db_index=True); video_id.minversion="0.10.3"  # unique key (per-user)
    youtube_id = models.CharField(max_length=20) # metadata only
    total_seconds_watched = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    language = models.CharField(max_length=8, blank=True, null=True); language.minversion="0.10.3"
    complete = models.BooleanField(default=False)
    completion_timestamp = models.DateTimeField(blank=True, null=True)
    completion_counter = models.IntegerField(blank=True, null=True)
    latest_activity_timestamp = models.DateTimeField(blank=True, null=True); latest_activity_timestamp.minversion="0.14.0"

    def __init__(self, *args, **kwargs):
        super(VideoLog, self).__init__(*args, **kwargs)
        self._unhashable_fields += ("latest_activity_timestamp",) # since it's being stripped out by minversion, we can't include it in the signature

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

    def save(self, *args, **kwargs):
        # To deal with backwards compatibility,
        #   check video_id, whether imported or not.
        if not self.video_id:
            assert kwargs.get("imported", False), "video_id better be set by internal code."
            assert self.youtube_id, "If not video_id, you better have set youtube_id!"
            video = get_video_from_youtube_id(self.youtube_id)
            self.video_id = video.get("id",
                                      self.youtube_id) if video else self.youtube_id  # for unknown videos, default to the youtube_id

        if not kwargs.get("imported", False):
            self.full_clean()

            try:
                UserLog.update_user_activity(self.user, activity_type="login", update_datetime=(self.completion_timestamp or datetime.now()), language=self.language)
            except ValidationError as e:
                logging.error("Failed to update userlog during video: %s" % e)

        super(VideoLog, self).save(*args, **kwargs)

    def get_uuid(self, *args, **kwargs):
        assert self.user is not None and self.user.id is not None, "User ID required for get_uuid"
        assert self.video_id is not None, "video_id is required for get_uuid"

        namespace = uuid.UUID(self.user.id)
        # can be video_id because that's set to the english youtube_id, to match past code.
        return uuid.uuid5(namespace, self.video_id.encode("utf-8")).hex

    @staticmethod
    def get_points_for_user(user):
        return VideoLog.objects.filter(user=user).aggregate(Sum("points")).get("points__sum", 0) or 0

    @classmethod
    def calc_points(cls, seconds_watched, video_length):
        return ceil(float(seconds_watched) / video_length* VideoLog.POINTS_PER_VIDEO)


class ExerciseLog(DeferredCountSyncedModel):
    user = models.ForeignKey(FacilityUser, blank=True, null=True, db_index=True)
    exercise_id = models.CharField(max_length=200, db_index=True)
    streak_progress = models.IntegerField(default=0)
    attempts = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    language = models.CharField(max_length=8, blank=True, null=True); language.minversion="0.10.3"
    complete = models.BooleanField(default=False)
    struggling = models.BooleanField(default=False)
    attempts_before_completion = models.IntegerField(blank=True, null=True)
    completion_timestamp = models.DateTimeField(blank=True, null=True)
    completion_counter = models.IntegerField(blank=True, null=True)
    latest_activity_timestamp = models.DateTimeField(blank=True, null=True); latest_activity_timestamp.minversion="0.14.0"

    def __init__(self, *args, **kwargs):
        super(ExerciseLog, self).__init__(*args, **kwargs)
        self._unhashable_fields += ("latest_activity_timestamp",) # since it's being stripped out by minversion, we can't include it in the signature

    class Meta:  # needed to clear out the app_name property from SyncedClass.Meta
        pass

    def __unicode__(self):
        return u"user=%s, exercise_id=%s, points=%d, language=%s%s" % (self.user, self.exercise_id, self.points, self.language, " (completed)" if self.complete else "")

    def save(self, *args, **kwargs):
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

    def get_attempt_logs(self):
        return AttemptLog.objects.filter(user=self.user, exercise_id=self.exercise_id, context_type__in=["playlist", "exercise"])


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
            start_datetime__lt=user_log.end_datetime,
            end_datetime__gte=user_log.end_datetime,
        )

        # Delete overlapping summaries because we know no better action. They
        # are not supposed to be there, but there are no database constraints.
        #
        # Added behavior in 0.16.7: We accumulate their counts and total_seconds
        # into the remaining log.
        overlapping_counts = 0
        overlapping_total_seconds = 0
        if log_summary.count() > 1:
            for log in log_summary[1:]:
                overlapping_counts += log.count
                overlapping_total_seconds += log.total_seconds
                log.soft_delete()

        # Get (or create) the log item
        log_summary = log_summary[0] if log_summary.count() else cls(
            device=device,
            user=user_log.user,
            activity_type=user_log.activity_type,
            language=user_log.language,
            start_datetime=cls.get_period_start_datetime(user_log.start_datetime, settings.USER_LOG_SUMMARY_FREQUENCY),
            end_datetime=cls.get_period_end_datetime(user_log.end_datetime, settings.USER_LOG_SUMMARY_FREQUENCY),
            total_seconds=0,
            count=0,
        )

        logging.debug("Adding %d seconds for %s/%s/%d/%s, period %s to %s" % (user_log.total_seconds, device.name, user_log.user.username, user_log.activity_type, user_log.language, log_summary.start_datetime, log_summary.end_datetime))

        # Add the latest info
        log_summary.total_seconds += overlapping_total_seconds + user_log.total_seconds
        log_summary.count += overlapping_counts + 1
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
    end_datetime = models.DateTimeField(
        blank=True,
        null=True,
        help_text=(
            "This field remains None until the time when the session ends then "
            "it's added to UserLogSummary."),
    )
    total_seconds = models.IntegerField(
        blank=True,
        null=True,
        help_text=(
            "This field remains None until the time when the session ends then "
            "it's added to UserLogSummary."),
    )

    @staticmethod
    def is_enabled():
        return getattr(settings, "USER_LOG_MAX_RECORDS_PER_USER", 0) != 0

    def __unicode__(self):
        if self.end_datetime:
            return u"%s (%s): logged in @ %s; for %s seconds" % (self.user.username, self.language, self.start_datetime, self.total_seconds)
        else:
            return u"%s (%s): logged in @ %s; last active @ %s" % (self.user.username, self.language, self.start_datetime, self.last_active_datetime)

    def save(self, *args, **kwargs):

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

        logs = cls.objects.exclude(end_datetime__gt="1900-01-01")
        logs = logs.filter(**kwargs)
        logs = logs.order_by("-last_active_datetime")
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


class AttemptLog(DeferredCountSyncedModel):
    """
    Detailed instances of user exercise engagement.
    """

    minversion = "0.13.0"

    user = models.ForeignKey(FacilityUser, db_index=True)
    exercise_id = models.CharField(max_length=200, db_index=True)
    seed = models.IntegerField(default=0)
    answer_given = models.TextField(blank=True) # first answer given to the question
    points = models.IntegerField(default=0)
    correct = models.BooleanField(default=False) # indicates that the first answer given was correct
    complete = models.BooleanField(default=False) # indicates that the question was eventually answered correctly
    context_type = models.CharField(max_length=20, blank=True) # e.g. "exam", "quiz", "playlist", "topic"
    context_id = models.CharField(max_length=100, blank=True) # e.g. the exam ID, quiz ID, playlist ID, topic ID, etc
    language = models.CharField(max_length=8, blank=True)
    timestamp = models.DateTimeField() # time at which the question was first loaded (that led to the initial response)
    time_taken = models.IntegerField(blank=True, null=True) # time spent on exercise before initial response (in ms)
    version = models.CharField(blank=True, max_length=100) # the version of KA Lite at the time the answer was given
    response_log = models.TextField(default="[]")
    response_count = models.IntegerField(default=0)
    assessment_item_id = models.CharField(max_length=100, blank=True, default="")

    class Meta:
        index_together = [
            ["user", "exercise_id", "context_type"],
        ]


class ContentLog(DeferredCountSyncedModel):

    minversion = "0.13.0"

    user = models.ForeignKey(FacilityUser, blank=True, null=True, db_index=True)
    content_id = models.CharField(max_length=200, db_index=True)
    points = models.IntegerField(default=0)
    language = models.CharField(max_length=8, blank=True, null=True); language.minversion="0.10.3"
    complete = models.BooleanField(default=False)
    start_timestamp = models.DateTimeField(auto_now_add=True, editable=False)  # this must NOT be null
    completion_timestamp = models.DateTimeField(blank=True, null=True)
    completion_counter = models.IntegerField(blank=True, null=True)
    time_spent = models.FloatField(blank=True, null=True)
    progress_timestamp = models.DateTimeField(blank=True, null=True)
    latest_activity_timestamp = models.DateTimeField(blank=True, null=True); latest_activity_timestamp.minversion="0.14.0"
    content_source = models.CharField(max_length=100, db_index=True, default=CHANNEL)
    content_kind = models.CharField(max_length=100, db_index=True)
    progress = models.FloatField(blank=True, null=True)
    views = models.IntegerField(blank=True, null=True)
    extra_fields = models.TextField(blank=True)

    def __init__(self, *args, **kwargs):
        super(ContentLog, self).__init__(*args, **kwargs)
        self._unhashable_fields += ("latest_activity_timestamp",) # since it's being stripped out by minversion, we can't include it in the signature

    class Meta:  # needed to clear out the app_name property from SyncedClass.Meta
        pass

    @staticmethod
    def get_points_for_user(user):
        return ContentLog.objects.filter(user=user).aggregate(Sum("points")).get("points__sum", 0) or 0

    def save(self, *args, **kwargs):
        if self.content_id and not self.complete:
            self.progress_timestamp = datetime.now()
        super(ContentLog, self).save(*args, **kwargs)

    def get_uuid(self):
        assert self.user is not None and self.user.id is not None, "User ID required for get_uuid"
        assert self.content_id is not None, "Content id required for get_uuid"
        assert self.content_kind is not None, "Content kind required for get_uuid"
        assert self.content_source is not None, "Content source required for get_uuid"

        namespace = uuid.UUID(self.user.id)
        hashtext = ":".join([self.__class__.__name__, self.content_source, self.content_kind, self.content_id])
        return uuid.uuid5(namespace, hashtext.encode("utf-8")).hex


# issue #5157
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
        # #5157 - why do we call this, is it superstition?
        instance.full_clean()
        # #5157
        end_time = instance.last_active_datetime or instance.end_datetime
        if end_time:
            instance.total_seconds = (end_time - instance.start_datetime).total_seconds()
        else:
            instance.total_seconds = 0

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


def logout_endlog(sender, request, user, **kwargs):
    if "facility_user" in request.session:
        # Logout, ignore any errors.
        try:
            UserLog.end_user_activity(request.session["facility_user"], activity_type="login")
        except ValidationError as e:
            logging.error("Failed to end_user_activity upon logout: %s" % e)
        del request.session["facility_user"]

# End a log whenever a logout event is fired.
user_logged_out.connect(logout_endlog)
