"""
Instead of re-writing the makemessages command built-in to Django, let's extend
it here.

For now (11/12/15) we'll just deal with the existing output. In the future, we
should revert makemessages to vanilla Django and again do our custom actions
*on top of* the vanilla output.
"""
from django.conf import settings
from django.core.management.commands import makemessages

logging = settings.LOG

IGNORE_PATTERNS = [
    "*/node_modules*",
    "*/LC_MESSAGES/*",
    "*/kalite/packages*",
    "*/kalite/static*",
    "*bundle*.js",
    "*/ka-lite/build/*",
    "*/js/i18n/*.js",
    "*/ka-lite/docs/*",
    "packages/dist",
]


class Command(makemessages.Command):

    def handle_noargs(self, *args, **options):
        # Set some sensible defaults
        options.setdefault("no_obsolete", True)
        
        for ignore_pattern in IGNORE_PATTERNS:
            if ignore_pattern not in options["ignore_patterns"]:
                options["ignore_patterns"].append(ignore_pattern)
        logging.debug("Ignoring the following patterns: {}".format(options["ignore_patterns"]))

        logging.debug("Calling base makemessages command.")
        super(Command, self).handle_noargs(*args, **options)
