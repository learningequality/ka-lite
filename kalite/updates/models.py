"""
"""
import datetime

from django.conf import settings; logging = settings.LOG
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import ugettext as _

from fle_utils.django_utils.classes import ExtendedModel


class UpdateProgressLog(ExtendedModel):
    """
    Gets progress
    """
    process_name = models.CharField(verbose_name=_("process name"), max_length=100)
    process_percent = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)], default=0)
    stage_name = models.CharField(verbose_name=_("stage name"), max_length=100, null=True)
    stage_percent = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)], default=0)
    current_stage = models.IntegerField(blank=True, null=True)
    stage_status = models.CharField(max_length=16, null=True)
    total_stages = models.IntegerField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True)
    completed = models.BooleanField(default=False)

    cancel_requested = models.BooleanField(default=False)

#    @classmethod
#    def get_or_create_log(process_name, *args, **kwargs):
#        try:
#            return UpdateProgressLog.objects.get(process_name=process_name, end_time=None)
#        except:
#            log = UpdateProgressLog(process_name=process_name, **kwargs)
#            log.save()
#            return log
    def __unicode__(self):
        return "%s (%5.2f%% done); stage %s (%4.1f%% done)%s" % (self.process_name, 100*self.process_percent, self.stage_name, 100*self.stage_percent, " completed" if self.completed else "")


    def save(self, *args, **kwargs):
        assert 0 <= self.stage_percent and self.stage_percent <= 1, "Stage percent must be between 0 and 1"
        assert 0 <= self.process_percent and self.process_percent <= 1, "Process percent must be between 0 and 1"
        super(UpdateProgressLog, self).save(*args, **kwargs)

    def restart(self):
        self.process_percent = 0
        self.stage_percent = 0
        self.current_stage = None  # 1 to len(stages)
        self.start_time = datetime.datetime.now()
        self.end_time = None
        self.completed = False
        self.save()

    def update_stage(self, stage_name, stage_percent, stage_status=None, notes=None):
        """
        Update a stage with it's percent, and process accordingly.

        stage_percent should be between 0 and 1
        """
        assert 0. <= stage_percent <= 1. or stage_percent is None, "stage percent must be between 0 and 1."
        assert self.end_time is None and self.completed == False, "Cannot update processes that have been ended."

        # When the stage name ends, then make sure to add a percent
        #   for whatever wasn't reported in finishing the previous stage,
        #   before adding in a percent for what's done for the current stage.
        #
        # Note that an empty stage_name means this is a pure update to
        #   the current stage, and so all this can be skipped.
        if stage_name and self.stage_name != stage_name:
            if self.stage_name:  # moving to the next stage
                self.notes = None  # reset notes after each stage
                self.current_stage += 1
            else: # just starting
                self.current_stage = 1
            self.stage_name = stage_name

        self.stage_percent = stage_percent if stage_percent is not None else self.stage_percent  # must be set before computing the process percent.
        self.process_percent = self._compute_process_percent()
        self.stage_status = stage_status
        self.notes = notes or self.notes
        self.save()


    def cancel_current_stage(self, stage_status=None, notes=None):
        """
        Delete the current stage--it's reported progress, and contribution to the total # of stages
        """
        logging.info("Cancelling stage %s of process %s" % (self.stage_name, self.process_name))

        self.stage_percent = 0.
        self.stage_name = None
        self.stage_status = stage_status or "cancelled"
        self.notes = notes
        self.process_percent = self._compute_process_percent()
        self.save()


    def update_total_stages(self, total_stages, current_stage=None):
        """
        Need to be careful, as this affects the computation of process_percent.
        """
        assert self.end_time is None and self.completed == False, "Cannot update processes that have been ended."

        # Wouldn't hurt to execute the logic below, but that debug message is ANNOYING :)
        if total_stages == self.total_stages:
            return

        if self.total_stages:
            logging.debug("Updating %s from %d to %d stages." % (self.process_name, self.total_stages, total_stages))
        else:
            logging.debug("Setting %s to %d total stages." % (self.process_name, total_stages))


        self.total_stages = total_stages
        if current_stage is not None:
            self.current_stage = current_stage
        self.process_percent = self._compute_process_percent()
        self.save()

    def _compute_process_percent(self):
        assert self.total_stages, "Must have set total_stages by now."
        return (self.stage_percent + (self.current_stage or 1) - 1) / float(self.total_stages)

    def cancel_progress(self, stage_status=None, notes=None):
        """
        Stamps end time.
        """
        logging.info("Cancelling process %s" % (self.process_name))

        self.stage_status = stage_status or "cancelled"
        self.end_time = datetime.datetime.now()
        self.completed=False
        self.notes = notes
        self.save()


    def mark_as_completed(self, stage_status=None, notes=None):
        """
        Completes stage and process percents, stamps end time.
        """
        logging.debug("Completing process %s" % (self.process_name))

        self.stage_percent = 1.
        self.process_percent = 1.
        self.current_stage = self.total_stages
        self.end_time = datetime.datetime.now()
        self.stage_status = stage_status or self.stage_status  # don't change this to None by default, so that users can be aware of any faults.
        self.completed = True
        self.notes = notes
        self.save()


    @classmethod
    def get_active_log(cls, create_new=True, force_new=False, overlapping=False, *args, **kwargs):
        """
        For a given query, return the most recently opened, non-closed log.
        """
        #assert not args, "no positional args allowed to this method."

        if not force_new:
            logs = cls.objects.filter(end_time=None, completed=False, **kwargs).order_by("-start_time")
            if logs.count() > 0:
                return logs[0]
            elif not create_new:
                return None

        if not "process_name" in kwargs:
            raise Exception("You better specify process_name if your log is not found!  Otherwise, how could we create one??")
        process_name = kwargs["process_name"]

        # Most of the time, we want exclusivity.
        if not overlapping:
            for old_log in cls.objects.filter(process_name=process_name, end_time=None):
                old_log.cancel_progress()

        log = cls(**kwargs)
        log.save()
        return log


class VideoFile(ExtendedModel):
    """
    Used exclusively for downloading files, and in conjunction with files on disk
    to determine what videos are available to users.
    """
    youtube_id = models.CharField(max_length=20, primary_key=True)
    flagged_for_download = models.BooleanField(default=False)
    download_in_progress = models.BooleanField(default=False)
    priority = models.IntegerField(default=0)
    percent_complete = models.IntegerField(default=0)
    cancel_download = models.BooleanField(default=False)
    language=models.CharField(max_length=8, default=settings.LANGUAGE_CODE)

    class Meta:
        ordering = ["priority", "youtube_id"]

    def __unicode__(self):
        if self.download_in_progress:
            status = "downloading (%d%%)" % self.percent_complete
        elif self.flagged_for_download:
            status = "waiting to download"
        elif self.percent_complete == 100:
            status = "downloaded"
        else:
            status = "not downloaded"
        return u"id: %s (%s)" % (self.youtube_id, status)
