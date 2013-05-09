import uuid
import logging

from annoying.functions import get_object_or_None
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

            # Mark user log
            UserLog.update_user_activity(self.user, activity_type="video", update_time=(self.completion_timestamp or datetime.now()))

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
                
            # Mark user log
            UserLog.update_user_activity(self.user, activity_type="exercise", update_time=(self.completion_timestamp or datetime.now()))
             
        super(ExerciseLog, self).save(*args, **kwargs)

    def get_uuid(self, *args, **kwargs):
        namespace = uuid.UUID(self.user.id)
        return uuid.uuid5(namespace, str(self.exercise_id)).hex

    @staticmethod
    def get_points_for_user(user):
        return ExerciseLog.objects.filter(user=user).aggregate(Sum("points")).get("points__sum", 0) or 0


class UserLog(SyncedModel):
    user = models.ForeignKey(FacilityUser, blank=True, null=True, db_index=True)
    login_time = models.DateTimeField(blank=False, null=False)
    last_activity_time = models.DateTimeField(blank=False, null=False)
    logout_time = models.DateTimeField(blank=True, null=True)
    total_time = models.IntegerField(blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if self.logout_time:
            self.full_clean()
            self.total_time = (self.logout_time-self.login_time).total_seconds()
            if self.total_time<0:
                import pdb; pdb.set_trace()
            logging.info("%s: total learning time: %d seconds"%(self.user.username,self.total_time)) 
        super(UserLog, self).save(*args, **kwargs)

#    def get_uuid(self, *args, **kwargs):
#        namespace = uuid.UUID(self.user.id)
#        return uuid.uuid5(namespace, str(self.exercise_id)).hex

    def __unicode__(self):
        if self.logout_time:
            return "%s: logged in @ %s; for %s seconds"%(self.user.username,self.login_time, self.total_time)
        else:
            return "%s: logged in @ %s; last active @ %s"%(self.user.username, self.login_time, self.last_activity_time)
            
    @staticmethod
    def update_user_activity(user, activity_type="update", update_time=None):
        if not user:
            raise Exception("user is None?")
        if not update_time:
            update_time = datetime.now()
                    
        cur_user_log_entry = get_object_or_None(UserLog, user=user, logout_time=None)

        if activity_type=="login":
            logging.info("%s: Logging LOGIN activity @ %s"%(user.username,update_time))
            
            # Seems we're logging in without logging out of the previous.
            #   Best thing to do is simulate a login
            #   at the previous last update time. 
            #
            # Note: this can be a recursive call
            if cur_user_log_entry:
                logging.warn("%s: Logging LOGOUT activity on a login @ %s"%(user.username,update_time))
                cur_user_log_entry.logout_time = cur_user_log_entry.last_activity_time
                cur_user_log_entry.save()
            
            # Create a new entry
            cur_user_log_entry = UserLog(user=user, login_time=update_time, last_activity_time=update_time)
            cur_user_log_entry.save()
        
        else:
            if not cur_user_log_entry:
                logging.warn("%s: Had to create a user log entry, but activity_type='%s'! @ %s"%(user.username,activity_type,update_time))
                cur_user_log_entry = UserLog(user=user, login_time=update_time, last_activity_time=update_time)
                cur_user_log_entry.save()
                
            if activity_type=="logout":
                logging.info("%s: Logging LOGOUT activity @ %s"%(user.username, update_time))
                cur_user_log_entry.logout_time = update_time
                cur_user_log_entry.save()
        
            else: # can accept any other type of activity
                logging.info("%s: Logging UPDATE activity (%s) @ %s"%(user.username,activity_type,update_time))
                cur_user_log_entry.last_activity_time = update_time
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







