import datetime

from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from settings import LOG as logging


class UpdateProgressLog(models.Model):
    """
    Gets progress
    """
    process_name = models.CharField(verbose_name="process name", max_length=100)
    process_percent = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)], default=0)
    stage_name = models.CharField(verbose_name="stage name", max_length=100, null=True)
    stage_percent = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)], default=0)
    total_stages = models.IntegerField(default=1)
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
        assert 0 <= self.stage_percent and self.stage_percent <= 1
        assert 0 <= self.process_percent and self.process_percent <= 1
        super(UpdateProgressLog, self).save(*args, **kwargs)

    def restart(self):
        self.process_percent = 0
        self.stage_percent = 0
        self.start_time = datetime.datetime.now()
        self.end_time = None
        self.completed = False
        self.save()

    def update_stage(self, stage_name, stage_percent, notes=None):
        """
        Update a stage with it's percent, and process accordingly.
        
        stage_percent should be between 0 and 1
        """
        assert 0. <= stage_percent <= 1., "stage percent must be between 0 and 1."
        assert self.end_time is None and self.completed == False, "Cannot update processes that have been ended."

        # When the stage name ends, then make sure to add a percent
        #   for whatever wasn't reported in finishing the previous stage,
        #   before adding in a percent for what's done for the current stage.
        if self.stage_name != stage_name:
            if self.stage_name:
                self.process_percent += (1 - self.stage_percent) / float(self.total_stages)
                self.stage_percent = 0
                self.notes = None  # reset notes after each stage
            self.stage_name = stage_name

        self.process_percent += (stage_percent - self.stage_percent) / float(self.total_stages)
        self.stage_percent = stage_percent
        self.notes = notes or self.notes
        self.save()


    def cancel_current_stage(self, notes=None):
        """
        Delete the current stage--it's reported progress, and contribution to the total # of stages
        """
        logging.info("Cancelling stage %s of process %s" % (self.stage_name, self.process_name))

        self.process_percent -= self.stage_percent / float(self.total_stages)
        self.stage_percent = 0.
        self.update_total_stages(self.total_stages - 1)
        self.stage_name = None
        self.notes = notes
        self.save()


    def update_total_stages(self, total_stages):
        """
        Need to be careful, as this affects the computation of process_percent.
        """
        assert self.end_time is None and self.completed == False, "Cannot update processes that have been ended."

        # Wouldn't hurt to execute the logic below, but that debug message is ANNOYING :)
        if total_stages == self.total_stages:
            return

        logging.debug("Updating %s from %d to %d stages." % (self.process_name, self.total_stages, total_stages))
        self.process_percent *= self.total_stages / float(total_stages) if total_stages > 0 else 0
        self.total_stages = total_stages
        self.save()


    def cancel_progress(self, notes=None):
        """
        Stamps end time.
        """
        logging.info("Cancelling process %s" % (self.process_name))

        self.end_time = datetime.datetime.now()
        self.completed=False
        self.notes = notes
        self.save()


    def mark_as_completed(self, notes=None):
        """
        Completes stage and process percents, stamps end time.
        """
        logging.debug("Completing process %s" % (self.process_name))

        self.stage_percent = 1.
        self.process_percent = 1.
        self.end_time = datetime.datetime.now()
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