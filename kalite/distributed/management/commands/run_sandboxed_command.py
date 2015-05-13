"""
"""
import sys

from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    """
    Gets input (that users could copy from our wiki) to run management commands.
    We could try to sandbox users, as well.
    """
    help = "Does raw_input, then launches a management command."

    # Allowable commands should be things that we have provided documentation for
    #   on the wiki, at http://kalitewiki.learningequality.org/user-s-manual/using-ka-lite/admins/run-management-commands
    allowable_commands = [
        "update", "apacheconfig", "cache",
        "retrypurgatory", "syncmodels",
        "changepassword", "createsuperuser",
        "dumpdata", "loaddata", "validate",
        "migrate",
    ]

    def handle(self, *args, **options):

        cmd = None
        while cmd not in self.allowable_commands:
            if cmd:
                sys.stderr.write("Command '%s' is not available.  Please choose from\n:" % cmd)
                sys.stderr.write("%s\n" % self.allowable_commands)
            cmd_text = raw_input("Please enter the command text to run: ")
            cmd = cmd_text.split(" ")[0]

        call_command(*cmd)