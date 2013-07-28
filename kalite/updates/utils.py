import sys

from django.core.management.base import BaseCommand, CommandError

from models import UpdateProgressLog


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

        super(UpdatesDynamicCommand, self).__init__(*args, **kwargs)


    def start(self, stage_name=None, notes=None):
        if not self.progress_log.total_stages:
            raise Exception("Must set num-stages (through __init__ or set_stages()) before starting.")

        self.progress_log.update_stage(stage_name=stage_name, stage_percent=0, notes=notes)


    def started(self):
        return self.progress_log.total_stages and not self.progress_log.completed


    def set_stages(self, num_stages=None):
        """
        Allow dynamic resetting of stages.
        """
        self.progress_log.update_total_stages(num_stages)


    def next_stage(self, stage_name=None, notes=None):
        """
        Allow dy
        """
        assert self.started(), "Must call start() before moving to a next stage!"
        self.progress_log.update_stage(stage_name=self.stage_name, stage_percent=1., notes=notes)


    def update_stage(self, stage_name, stage_percent, notes=None):
        self.progress_log.update_stage(stage_name=stage_name, stage_percent=stage_percent, notes=notes)


    def cancel(self, notes=None):
        self.progress_log.cancel_progress(notes=notes)


    def complete(self, notes=None):
        self.progress_log.mark_as_completed(notes=notes)


class UpdatesStaticCommand(BaseCommand):
    """
    Command that updates the UpdateProgressLog table,
    having a well-defined, sequential static list of stages.
    """
    def __init__(self, process_name=None, *args, **kwargs):
        self.process_name = process_name or self.__class__.__module__.split(".")[-1]
        self.progress_log = UpdateProgressLog.get_active_log(process_name=self.process_name)
        self.stage_index = None

        super(UpdatesStaticCommand, self).__init__(*args, **kwargs)


    def start(self, notes=None):
        assert self.stages
        assert self.stage_index is None

        self.stage_index = 0
        self.progress_log.update_total_stages(len(self.stages))
        self.progress_log.update_stage(stage_name=self.stages[self.stage_index], stage_percent=0)

        if notes:
            sys.stdout.write("%s\n" % notes)


    def started(self):
        return self.stage_index is not None


    def next_stage(self, notes=None):
        """
        Allow dy
        """
        assert self.stage_index is not None, "Must call start function before next_stage()"
        self.stage_index += 1
        self.progress_log.update_stage(stage_name=self.stages[self.stage_index], stage_percent=0)

        if notes:
            sys.stdout.write("%s\n" % notes)


    def update_stage(self, stage_percent, notes=None):
        self.progress_log.update_stage(stage_name=self.stages[self.stage_index], stage_percent=stage_percent)
        if notes:
            sys.stdout.write("%s\n" % notes)


    def cancel(self, notes=None):
        self.progress_log.cancel_progress(notes=notes)
        self.stage_index = None


    def complete(self, notes=None):
        self.progress_log.mark_as_completed(notes=notes)
        self.stage_index = None

