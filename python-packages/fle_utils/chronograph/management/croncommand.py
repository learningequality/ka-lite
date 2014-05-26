"""
Defines CronCommand, an abstract Command class
"""
import sys
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class CronCommand(BaseCommand):
    """Cron commands are commands that can be called programmatically, but not from the command-line.

    Why you'd want this: to interact with chronograph easily, but to force the command to be run within the server process.
    """

    unique_option_list = (
        make_option('--commandline', action='store_true', dest='force_commandline', default=False,
            help='Forces the command to be run from the command-line.'),
        )
    option_list = BaseCommand.option_list + unique_option_list

    def __init__(self, *args, **kwargs):
        super(CronCommand, self).__init__(*args, **kwargs)
        self.ok_to_run = True
        self.stderr = sys.stderr  # necessary default... Django!!
        self.stdout = sys.stdout

    def run_from_argv(self, *args, **kwargs):
        # Rather than erroring here, save the flag so that
        #   when we throw, it can be caught and displayed nicely
        #   to the user.  If we throw here, it gets ugly :(
        self.ok_to_run = bool(set(['--commandline', '--help']).intersection(set(args[0])))
        super(CronCommand, self).run_from_argv(*args, **kwargs)

    def execute(self, *args, **kwargs):
        if self.ok_to_run:
            super(CronCommand, self).execute(*args, **kwargs)
        else:
            raise CommandError("This command cannot be run from the command-line.")
