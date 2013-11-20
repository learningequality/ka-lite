import sys

from django.core.management.base import BaseCommand, CommandError

from updates.models import UpdateProgressLog

class UpdatesCommand(BaseCommand):
    """
    Abstract class for sharing code across Dynamic and Static versions
    """
    def __init__(self, process_name=None, *args, **kwargs):
        self.process_name = process_name or self.__class__.__module__.split(".")[-1]
        self.progress_log = UpdateProgressLog.get_active_log(process_name=self.process_name)

        super(UpdatesCommand, self).__init__(*args, **kwargs)

    def display_notes(self, notes, ignore_same=True):
            if notes and (not ignore_same or notes != self.progress_log.notes):
                self.stdout.write("%s\n" % notes)


class UpdatesDynamicCommand(UpdatesCommand):
    """
    Command that updates the UpdateProgressLog table,
    without having a full, static list of stages.

    Updates by knowing the current total number of stages (which can change),

    """
    def __init__(self, num_stages=None, *args, **kwargs):
        super(UpdatesDynamicCommand, self).__init__(*args, **kwargs)
        if num_stages:
            self.set_stages(num_stages=num_stages)

    def start(self, stage_name=None, notes=None):
        if not self.progress_log.total_stages:
            raise Exception("Must set num-stages (through __init__ or set_stages()) before starting.")
        self.check_if_cancel_requested()
        self.progress_log.update_stage(stage_name=stage_name, stage_percent=0, notes=notes)
        self.display_notes(notes, ignore_same=False)

    def started(self):
        self.check_if_cancel_requested()
        return self.progress_log.total_stages and not self.progress_log.completed

    def set_stages(self, num_stages=None, notes=None):
        """
        Allow dynamic resetting of stages.
        """
        self.check_if_cancel_requested()
        self.progress_log.update_total_stages(num_stages)
        self.display_notes(notes)

    def next_stage(self, stage_name=None, notes=None):
        assert self.started(), "Must call start() before moving to a next stage!"
        self.check_if_cancel_requested()
        self.progress_log.update_stage(stage_name=self.stage_name, stage_percent=1., notes="Completed.")
        self.stage_name = stage_name
        self.display_notes(notes or "")

    def update_stage(self, stage_name, stage_percent, notes=None):
        self.check_if_cancel_requested()
        self.progress_log.update_stage(stage_name=stage_name, stage_percent=stage_percent, notes=notes)
        self.display_notes(notes)

    def cancel(self, notes=None):
        self.check_if_cancel_requested()
        self.progress_log.cancel_progress(notes=notes)
        self.display_notes(notes)

    def complete(self, notes=None):
        self.check_if_cancel_requested()
        self.progress_log.mark_as_completed(notes=notes)
        self.display_notes(notes)

    def check_if_cancel_requested(self):
        if self.progress_log.cancel_requested:
            self.progress_log.end_time = datetime.datetime.now()
            self.progress_log.save()
            raise CommandException("Process cancelled.")


class UpdatesStaticCommand(UpdatesCommand):
    """
    Command that updates the UpdateProgressLog table,
    having a well-defined, sequential static list of stages.
    """
    def __init__(self, *args, **kwargs):
        super(UpdatesStaticCommand, self).__init__(*args, **kwargs)
        self.stage_index = None

    def start(self, notes=None):
        assert self.stages, "Stages must be set before starting."
        assert self.stage_index is None, "Must not call start while already in progress."

        self.stage_index = 0
        self.progress_log.update_total_stages(len(self.stages))
        self.progress_log.update_stage(stage_name=self.stages[self.stage_index], stage_percent=0, notes=notes)
        self.display_notes(notes, ignore_same=False)

    def restart(self, notes=None):
        self.progress_log.restart()
        self.start(notes=notes)
        self.display_notes(notes)

    def started(self):
        return self.stage_index is not None

    def next_stage(self, notes=None):
        assert self.stage_index is not None, "Must call start function before next_stage()"
        self.stage_index += 1
        self.progress_log.update_stage(stage_name=self.stages[self.stage_index], stage_percent=0, notes=notes)
        self.display_notes(notes)

    def update_stage(self, stage_percent, notes=None):
        self.progress_log.update_stage(stage_name=self.stages[self.stage_index], stage_percent=stage_percent, notes=notes)
        self.display_notes(notes)

    def cancel(self, notes=None):
        self.progress_log.cancel_progress(notes=notes)
        self.stage_index = None
        self.display_notes(notes)

    def complete(self, notes=None):
        self.progress_log.mark_as_completed(notes=notes)
        self.stage_index = None
        self.display_notes(notes)
