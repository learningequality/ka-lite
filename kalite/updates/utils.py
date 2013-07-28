from django.core.management.base import BaseCommand, CommandError

from models import UpdateProgressLog


class UpdatesCommandError(CommandError):
    def __init__(self, progress_log, *args, **kwargs):
        progress_log.cancel_progress()
        super(UpdatesCommandError, self).__init__(*args, **kwargs)


class UpdatesDynamicCommand(BaseCommand):
    """
    Command that updates the UpdateProgressLog table,
    without having a full, static list of stages.
    
    Updates by knowing the current total number of stages (which can change),
    
    """
    def __init__(self, process_name=None, num_stages=None, *args, **kwargs):
        self.process_name = process_name or self.__class__.__module__.split(".")[-1]
        self.progress_log = UpdateProgressLog.get_active_log(process_name=self.process_name)

        if num_stages:
            self.set_stages(num_stages=num_stages)

        super(BaseCommand, self).__init__(*args, **kwargs)


    def start(self, stage_name=None):
        if not self.progress_log.total_stages:
            raise Exception("Must set num-stages (through __init__ or set_stages()) before starting.")

        self.progress_log.update_stage(stage_name=stage_name, stage_percent=0)


    def started(self):
        return self.progress_log.total_stages and not self.progress_log.completed


    def set_stages(self, num_stages=None):
        """
        Allow dynamic resetting of stages.
        """
        self.progress_log.update_total_stages(num_stages)


    def next_stage(self, stage_name=None):
        """
        Allow dy
        """
        assert self.stage_index is not None, "Must call start function before next_stage()"
        self.progress_log.update_stage(stage_name=self.stage_name, stage_percent=1.)


    def update_stage(self, stage_name, stage_percent):
        self.progress_log.update_stage(stage_name=stage_name, stage_percent=stage_percent)

    def cancel(self):
        self.progress_log.cancel_progress()


    def complete(self):
        self.progress_log.mark_as_completed()

