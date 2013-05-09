import uuid
import logging

from annoying.functions import get_object_or_None, isnumeric
from datetime import datetime

from django.db import models
from django.db.models import Sum, Avg
from django.contrib.auth.decorators import login_required

import settings
from securesync.models import SyncedModel, FacilityUser, Device

logging.getLogger().setLevel(logging.INFO)

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


class UserLog(SyncedModel):
    KNOWN_TYPES={"login": 1}
    user = models.ForeignKey(FacilityUser, blank=True, null=True, db_index=True)
    activity_type = models.IntegerField(blank=False, null=False)
    start_time = models.DateTimeField(blank=False, null=False)
    last_active_time = models.DateTimeField(blank=False, null=False)
    end_time = models.DateTimeField(blank=True, null=True)
    total_time = models.IntegerField(blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if self.end_time:
            self.full_clean()
            self.total_time = (self.end_time-self.start_time).total_seconds()
            if self.total_time<0:
                import pdb; pdb.set_trace()
            logging.info("%s: total learning time: %d seconds"%(self.user.username,self.total_time)) 
        super(UserLog, self).save(*args, **kwargs)

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

        logging.info("%s: BEGIN activity(%d) @ %s"%(user.username, activity_type, start_time))
        
        # Seems we're logging in without logging out of the previous.
        #   Best thing to do is simulate a login
        #   at the previous last update time. 
        #
        # Note: this can be a recursive call
        if cur_user_log_entry:
            logging.warn("%s: END activity on a begin @ %s"%(user.username,start_time))
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
            logging.warn("%s: Had to create a user log entry, but UPDATING('%d')! @ %s"%(user.username,activity_type,update_time))
            cur_user_log_entry = UserLog.begin_user_activity(user=user, activity_type=activity_type, start_time=update_time)
            
        logging.info("%s: UPDATE activity (%d) @ %s"%(user.username,activity_type,update_time))
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
            logging.warn("%s: Had to create a user log entry, but STOPPING('%d')! @ %s"%(user.username,activity_type,end_time))
            cur_user_log_entry = UserLog.begin_user_activity(user=user, activity_type=activity_type, start_time=end_time)

        logging.info("%s: Logging LOGOUT activity @ %s"%(user.username, end_time))
        cur_user_log_entry.end_time = end_time
        cur_user_log_entry.save()

            
settings.add_syncing_models([VideoLog, ExerciseLog, UserLog])

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







