import uuid
from datetime import datetime
from annoying.functions import get_object_or_None
from dateutil import relativedelta

from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Sum, Avg

import settings
from securesync import model_sync
from securesync.models import SyncedModel, FacilityUser, Device
from utils.functions import isnumeric


class VideoLog(SyncedModel):
    user = models.ForeignKey(FacilityUser, blank=True, null=True, db_index=True)
    youtube_id = models.CharField(max_length=20, db_index=True)
    total_seconds_watched = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    complete = models.BooleanField(default=False)
    completion_timestamp = models.DateTimeField(blank=True, null=True)
    completion_counter = models.IntegerField(blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not kwargs.get("imported", False):
            self.full_clean()
            
            # Compute learner status
            already_complete = self.complete
            self.complete = (self.points >= 750)
            if not already_complete and self.complete:
                self.completion_timestamp = datetime.now()
                self.completion_counter = Device.get_own_device().get_counter()

            # Tell logins that they are still active.
            #   TODO(bcipolli): Could log video information in the future.
            UserLog.update_user_activity(self.user, activity_type="login", update_time=(self.completion_timestamp or datetime.now()))

        super(VideoLog, self).save(*args, **kwargs)
    
    def get_uuid(self, *args, **kwargs):
        namespace = uuid.UUID(self.user.id)
        return uuid.uuid5(namespace, str(self.youtube_id)).hex

    @staticmethod
    def get_points_for_user(user):
        return VideoLog.objects.filter(user=user).aggregate(Sum("points")).get("points__sum", 0) or 0


class ExerciseLog(SyncedModel):
    user = models.ForeignKey(FacilityUser, blank=True, null=True, db_index=True)
    exercise_id = models.CharField(max_length=100, db_index=True)
    streak_progress = models.IntegerField(default=0)
    attempts = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    complete = models.BooleanField(default=False)
    struggling = models.BooleanField(default=False)
    attempts_before_completion = models.IntegerField(blank=True, null=True)
    completion_timestamp = models.DateTimeField(blank=True, null=True)
    completion_counter = models.IntegerField(blank=True, null=True)
    
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
                self.completion_counter = Device.get_own_device().get_counter()
                self.attempts_before_completion = self.attempts
                
            # Tell logins that they are still active.
            #   TODO(bcipolli): Could log exercise information in the future.
            UserLog.update_user_activity(self.user, activity_type="login", update_time=(self.completion_timestamp or datetime.now()))
             
        super(ExerciseLog, self).save(*args, **kwargs)

    def get_uuid(self, *args, **kwargs):
        namespace = uuid.UUID(self.user.id)
        return uuid.uuid5(namespace, str(self.exercise_id)).hex

    @staticmethod
    def get_points_for_user(user):
        return ExerciseLog.objects.filter(user=user).aggregate(Sum("points")).get("points__sum", 0) or 0


class UserLogSummary(SyncedModel):
    """Like UserLogs, but summarized over a period of time.  Unique per user, device, and activity_type"""
    device = models.ForeignKey(Device)
    user = models.ForeignKey(FacilityUser, blank=True, null=True, db_index=True)
    activity_type = models.IntegerField(blank=False, null=False)
    start_time = models.DateTimeField(blank=False, null=False)
    end_time = models.DateTimeField(blank=True, null=True)
    total_time = models.IntegerField(blank=True, null=True)

    def __unicode__(self):
        return "%d seconds for %s/%s/%d, period %s to %s" % (self.total_time, self.device.name, self.user.username, self.activity_type, self.start_time, self.end_time)



    @staticmethod
    def get_period_start_time(log_time, summary_freq):
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


    @staticmethod
    def get_period_end_time(log_time, summary_freq):
        start_time = UserLogSummary.get_period_start_time(log_time, summary_freq)
        summary_freq_qty    = summary_freq[0]
        summary_freq_period = summary_freq[1].lower()

        if summary_freq_period in ["day", "days"]:
            return start_time + relativedelta.relativedelta(days=summary_freq_qty) - relativedelta.relativedelta(seconds=1)

        elif summary_freq_period in ["week", "weeks"]:
            return start_time + relativedelta.relativedelta(days=7*summary_freq_qty) - relativedelta.relativedelta(seconds=1)

        elif summary_freq_period in ["month", "months"]:
            return start_time + relativedelta.relativedelta(months=summary_freq_qty) - relativedelta.relativedelta(seconds=1)

        elif summary_freq_period in ["year", "years"]:
            return start_time + relativedelta.relativedelta(years=summary_freq_qty) - relativedelta.relativedelta(seconds=1)

        else:
            raise NotImplementedError("Unrecognized summary frequency period: %s" % summary_freq_period)


    @classmethod 
    def add_log_to_summary(cls, user_log, device=Device.get_own_device()):
        assert user_log.end_time, "all log items must have an end_time to be saved here."
        assert user_log.total_time >= 0, "all log items must have a non-negative total_time to be saved here."
        
        # Check for an existing object
        log_summary = cls.objects.filter(
            device=device,
            user=user_log.user,
            activity_type=user_log.activity_type,
            start_time__lte=user_log.end_time,
            end_time__gte=user_log.end_time,
        )
        assert log_summary.count() <= 1, "There should never be multiple summaries in the same time period/device/user/type combo"

        # Get the log item
        log_summary = log_summary[0] if log_summary.count() else cls(
            device=device,
            user=user_log.user,
            activity_type=user_log.activity_type,
            start_time=cls.get_period_start_time(user_log.end_time, settings.USER_LOG_SUMMARY_FREQUENCY),
            end_time=cls.get_period_end_time(user_log.end_time, settings.USER_LOG_SUMMARY_FREQUENCY),
            total_time=0,
        )

        settings.LOG.debug("Adding %d seconds for %s/%s/%d, period %s to %s" % (user_log.total_time, device.name, user_log.user.username, user_log.activity_type, log_summary.start_time, log_summary.end_time))

        # Add the latest info
        log_summary.total_time += user_log.total_time
        log_summary.save()


class UserLog(models.Model):  # Not sync'd, only summaries are
    KNOWN_TYPES={"login": 1}
    user = models.ForeignKey(FacilityUser, blank=True, null=True, db_index=True)
    activity_type = models.IntegerField(blank=False, null=False)
    start_time = models.DateTimeField(blank=False, null=False)
    last_active_time = models.DateTimeField(blank=False, null=False)
    end_time = models.DateTimeField(blank=True, null=True)
    total_time = models.IntegerField(blank=True, null=True)
    
    def save(self, *args, **kwargs):
        add_to_summary = False
        
        # Compute total_time, save to summary
        #   Note: only supports setting end_time once!
        if self.end_time and not self.total_time:
            self.full_clean()
            self.total_time = (self.end_time-self.start_time).total_seconds()
            settings.LOG.info("%s: total learning time: %d seconds"%(self.user.username,self.total_time))
            assert self.total_time >= 0, "Total learning time should always be non-negative."
            add_to_summary = True
        super(UserLog, self).save(*args, **kwargs)

        # Save only successfully saved, completed log items to the UserLogSummary
        if add_to_summary:
            UserLogSummary.add_log_to_summary(self)

        if UserLog.objects.count() > settings.USER_LOG_MAX_RECORDS:
            # Unfortunately, could not do an aggregate delete when doing a 
            #   slice in query
            for user_log in UserLog.objects.all().order_by("start_time")[0:UserLog.objects.count()-settings.USER_LOG_MAX_RECORDS]:
                user_log.delete()

#    def get_uuid(self, *args, **kwargs):
#        namespace = uuid.UUID(self.user.id)
#        return uuid.uuid5(namespace, str(self.exercise_id)).hex

    def __unicode__(self):
        if self.end_time:
            return "%s: logged in @ %s; for %s seconds"%(self.user.username,self.start_time, self.total_time)
        else:
            return "%s: logged in @ %s; last active @ %s"%(self.user.username, self.start_time, self.last_active_time)
    
    @staticmethod
    def get_activity_int(activity_type):
        """Helper function converts from string or int to the underlying int"""
        if activity_type.__class__.__name__=="str":
            if activity_type in UserLog.KNOWN_TYPES:
                return UserLog.KNOWN_TYPES[activity_type]
            else:
                raise Exception("Unrecognized activity type: %s"%activity_type)
        elif isnumeric(activity_type):
            return int(activity_type)
        else:
            raise Exception("Cannot convert requested activity_type to int")
            
            
    @staticmethod
    def begin_user_activity(user, activity_type="login", start_time=None):
        activity_type = UserLog.get_activity_int(activity_type)
        if not start_time: start_time = datetime.now()
        if not user:       raise Exception("user is None?")
    
        cur_user_log_entry = get_object_or_None(UserLog, user=user, end_time=None)

        settings.LOG.info("%s: BEGIN activity(%d) @ %s"%(user.username, activity_type, start_time))
        
        # Seems we're logging in without logging out of the previous.
        #   Best thing to do is simulate a login
        #   at the previous last update time. 
        #
        # Note: this can be a recursive call
        if cur_user_log_entry:
            settings.LOG.warn("%s: END activity on a begin @ %s"%(user.username,start_time))
            UserLog.end_user_activity(user=user, activity_type=activity_type, end_time=cur_user_log_entry.last_active_time)
        
        # Create a new entry
        cur_user_log_entry = UserLog(user=user, activity_type=activity_type, start_time=start_time, last_active_time=start_time)
        cur_user_log_entry.save()
        
        return cur_user_log_entry


    @staticmethod
    def update_user_activity(user, activity_type="login", update_time=None):
        activity_type = UserLog.get_activity_int(activity_type)
        if not update_time: update_time = datetime.now()
        if not user:        raise Exception("user is None?")

        cur_user_log_entry = get_object_or_None(UserLog, user=user, end_time=None)

        # No unstopped starts.  Start should have been called first!
        if not cur_user_log_entry:
            settings.LOG.warn("%s: Had to create a user log entry, but UPDATING('%d')! @ %s"%(user.username,activity_type,update_time))
            cur_user_log_entry = UserLog.begin_user_activity(user=user, activity_type=activity_type, start_time=update_time)
            
        settings.LOG.info("%s: UPDATE activity (%d) @ %s"%(user.username,activity_type,update_time))
        cur_user_log_entry.last_active_time = update_time
        cur_user_log_entry.save()


    @staticmethod
    def end_user_activity(user,    activity_type="login", end_time=None):
        activity_type = UserLog.get_activity_int(activity_type)
        if not end_time:   end_time = datetime.now()
        if not user:       raise Exception("user is None?")
                    
        cur_user_log_entry = get_object_or_None(UserLog, user=user, end_time=None)

        # No unstopped starts.  Start should have been called first!
        if not cur_user_log_entry:
            settings.LOG.warn("%s: Had to create a user log entry, but STOPPING('%d')! @ %s"%(user.username,activity_type,end_time))
            cur_user_log_entry = UserLog.begin_user_activity(user=user, activity_type=activity_type, start_time=end_time)

        settings.LOG.info("%s: Logging LOGOUT activity @ %s"%(user.username, end_time))
        cur_user_log_entry.end_time = end_time
        cur_user_log_entry.save()


class VideoFile(models.Model):
    youtube_id = models.CharField(max_length=20, primary_key=True)
    flagged_for_download = models.BooleanField(default=False)
    flagged_for_subtitle_download = models.BooleanField(default=False)
    download_in_progress = models.BooleanField(default=False)
    subtitle_download_in_progress = models.BooleanField(default=False)
    priority = models.IntegerField(default=0)
    percent_complete = models.IntegerField(default=0)
    subtitles_downloaded = models.BooleanField(default=False)
    cancel_download = models.BooleanField(default=False)
    
    class Meta:
        ordering = ["priority", "youtube_id"]


class LanguagePack(models.Model):
    lang_id = models.CharField(max_length=5, primary_key=True)
    lang_version = models.CharField(max_length=5)
    software_version = models.CharField(max_length=12)
    lang_name = models.CharField(max_length=30)


model_sync.add_syncing_models([VideoLog, ExerciseLog, UserLogSummary])
