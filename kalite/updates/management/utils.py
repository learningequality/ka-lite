"""
"""
from datetime import datetime
from optparse import make_option

from django.conf import settings; logging = settings.LOG
from django.utils.translation import ugettext as _

from ..models import UpdateProgressLog
from fle_utils.django_utils.command import LocaleAwareCommand
from functools import wraps


def skip_if_no_progress_log(func):
    @wraps(func)
    def check(self, *args, **kwargs):
        if not self.progress_log:
            return
        return func(self, *args, **kwargs)

    return check


class UpdatesCommand(LocaleAwareCommand):
    """
    Abstract class for sharing code across Dynamic and Static versions
    """
    option_list = LocaleAwareCommand.option_list + (
        make_option(
            "", "--foreground",
            action="store_true",
            dest="foreground",
            default=False,
            help=(
                "Run the command without job scheduler and  database-backed "
                "progress. Used when you retrieve a content pack before "
                "initializing KA Lite's db."
            )),
    )

    def __init__(self, process_name=None, *args, **kwargs):

        self.process_name = process_name or self.__class__.__module__.split(".")[-1]

        super(UpdatesCommand, self).__init__(*args, **kwargs)

    def setup(self, options):

        # Should be set by command's handle() method since there's no clear
        # call structure defined. Respected by the methods that update stuff
        # in the database.
        self.foreground = options["foreground"]

        if not self.foreground:
            self.progress_log = UpdateProgressLog.get_active_log(process_name=self.process_name)
        else:
            self.progress_log = None
        if self.progress_log and self.progress_log.current_stage:
            self.progress_log.cancel_progress(notes=_("Starting fresh."))
            self.progress_log = UpdateProgressLog.get_active_log(process_name=self.process_name)

    @skip_if_no_progress_log
    def display_notes(self, notes, ignore_same=True):
        if notes and (not ignore_same or notes != self.progress_log.notes):
            logging.info(notes)

    @skip_if_no_progress_log
    def ended(self):
        return self.progress_log.end_time is not None


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

    @skip_if_no_progress_log
    def start(self, stage_name=None, notes=None):
        if not self.progress_log.total_stages:
            raise Exception("Must set num-stages (through __init__ or set_stages()) before starting.")
        self.check_if_cancel_requested()
        self.display_notes(notes, ignore_same=False)
        self.progress_log.update_stage(stage_name=stage_name, stage_percent=0, notes=notes)

    @skip_if_no_progress_log
    def started(self):
        self.check_if_cancel_requested()
        return self.progress_log.total_stages and not self.progress_log.completed

    @skip_if_no_progress_log
    def set_stages(self, num_stages=None, notes=None):
        """
        Allow dynamic resetting of stages.
        """
        self.check_if_cancel_requested()
        self.display_notes(notes)
        self.progress_log.update_total_stages(num_stages)

    @skip_if_no_progress_log
    def next_stage(self, stage_name=None, notes=None):
        assert self.started(), "Must call start() before moving to a next stage!"
        self.check_if_cancel_requested()
        self.display_notes(notes or "")  # blank out old notes, if necessary
        self.update_stage(stage_name=stage_name, stage_percent=0., notes=notes)

    @skip_if_no_progress_log
    def update_stage(self, stage_name=None, stage_percent=None, stage_status=None, notes=None):
        self.check_if_cancel_requested()
        self.display_notes(notes)
        self.progress_log.update_stage(stage_name=stage_name, stage_percent=stage_percent, stage_status=stage_status, notes=notes)

    @skip_if_no_progress_log
    def cancel(self, stage_status=None, notes=None):
        self.check_if_cancel_requested()
        self.display_notes(notes)
        self.progress_log.cancel_progress(stage_status=stage_status, notes=notes)

    @skip_if_no_progress_log
    def complete(self, notes=None):
        self.check_if_cancel_requested()
        self.display_notes(notes)
        self.progress_log.mark_as_completed(notes=notes)

    @skip_if_no_progress_log
    def check_if_cancel_requested(self):
        if self.progress_log.cancel_requested:
            self.progress_log.end_time = datetime.now()
            self.progress_log.save()
            raise RuntimeError("Process cancelled.")


class UpdatesStaticCommand(UpdatesCommand):
    """
    Command that updates the UpdateProgressLog table,
    having a well-defined, sequential static list of stages.
    """
    def __init__(self, *args, **kwargs):
        super(UpdatesStaticCommand, self).__init__(*args, **kwargs)

    @skip_if_no_progress_log
    def start(self, notes=None):
        assert self.stages, "Stages must be set before starting."
        assert self.progress_log.current_stage is None, "Must not call start while already in progress."
        self.progress_log.update_total_stages(len(self.stages))
        self.display_notes(notes, ignore_same=False)
        self.progress_log.update_stage(stage_name=self.stages[0], stage_percent=0, notes=notes)

    @skip_if_no_progress_log
    def restart(self, notes=None):
        self.progress_log.restart()
        self.display_notes(notes)
        self.start(notes=notes)

    @skip_if_no_progress_log
    def started(self):
        return self.progress_log.current_stage is not None

    @skip_if_no_progress_log
    def next_stage(self, notes=None):
        assert self.progress_log.current_stage is not None, "Must call start function before next_stage()"
        assert self.progress_log.current_stage < len(self.stages), "Must not be at the last stage already."
        self.display_notes(notes)
        self.progress_log.update_stage(stage_name=self.stages[self.progress_log.current_stage], stage_percent=0, notes=notes)

    @skip_if_no_progress_log
    def update_stage(self, stage_percent, stage_status=None, notes=None):
        self.display_notes(notes)
        self.progress_log.update_stage(stage_name=self.stages[self.progress_log.current_stage - 1], stage_percent=stage_percent, stage_status=stage_status, notes=notes)

    @skip_if_no_progress_log
    def cancel(self, stage_status=None, notes=None):
        self.display_notes(notes)
        self.progress_log.cancel_progress(stage_status=stage_status, notes=notes)

    @skip_if_no_progress_log
    def complete(self, notes=None):
        self.display_notes(notes)
        self.progress_log.mark_as_completed(notes=notes)
