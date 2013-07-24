import datetime

from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from settings import LOG as logging


class UpdateProgressLog(models.Model):
    """
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


    def update_stage(self, stage_name, stage_percent):
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
            self.stage_name = stage_name

        self.process_percent += (stage_percent - self.stage_percent) / float(self.total_stages)
        self.stage_percent = stage_percent
        self.save()


    def cancel_current_stage(self):
        """
        Delete the current stage--it's reported progress, and contribution to the total # of stages
        """
        logging.info("Cancelling stage %s of process %s" % (self.stage_name, self.process_name))

        self.process_percent -= self.stage_percent / float(self.total_stages)
        self.stage_percent = 0.
        self.update_total_stages(self.total_stages - 1)
        self.stage_name = None
        self.save()


    def update_total_stages(self, total_stages):
        """
        Need to be careful, as this affects the computation of process_percent.
        """
        assert self.end_time is None and self.completed == False, "Cannot update processes that have been ended."
        logging.debug("Updating %s from %d to %d stages." % (self.process_name, self.total_stages, total_stages))

        self.process_percent *= self.total_stages / float(total_stages) if total_stages > 0 else 0
        self.total_stages = total_stages
        self.save()


    def cancel_progress(self):
        """
        Stamps end time.
        """
        logging.info("Cancelling process %s" % (self.process_name))

        self.end_time = datetime.datetime.now()
        self.completed=False
        self.save()


    def mark_as_completed(self):
        """
        Completes stage and process percents, stamps end time.
        """
        logging.debug("Completing process %s" % (self.process_name))

        self.stage_percent = 1.
        self.process_percent = 1.
        self.end_time = datetime.datetime.now()
        self.completed = True
        self.save()
