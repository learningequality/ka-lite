"""
Instead of re-writing the makemessages command built-in to Django, let's extend
it here.

For now (11/12/15) we'll just deal with the existing output. In the future, we
should revert makemessages to vanilla Django and again do our custom actions
*on top of* the vanilla output.
"""
import logging
import re
import os

from django.core.management.commands import makemessages

logger = logging.getLogger(__name__)

# This is done through an environment because there is a bug in Django or
# somewhere else such that setting --ignore multiple times does not work!
# Default: Ignore everything - great for our tests
IGNORE_PATTERNS = os.environ.get("IGNORE_PATTERNS", "foo,bar").split(",")

class Command(makemessages.Command):

    def handle_noargs(self, *args, **options):
        
        for ignore_pattern in IGNORE_PATTERNS:
            if ignore_pattern not in options["ignore_patterns"]:
                options["ignore_patterns"].append(ignore_pattern)
        logger.debug("Ignoring the following patterns: {}".format(options["ignore_patterns"]))

        logger.debug("Calling base makemessages command.")
        super(Command, self).handle_noargs(*args, **options)

        # Make all the path annotations relative
        domain = options.get('domain', "django")
        django_po = os.path.join(
            os.getcwd(),
            "locale",
            "en",
            "LC_MESSAGES",
            domain + ".po"
        )
        
        msgid_re = re.compile(r"^\#\:\s+(.+)kalite.+\:\d+\s*$", re.MULTILINE)
        
        contents = open(django_po, "r").read()
        matches = msgid_re.search(contents)
        if not matches:
            raise RuntimeError("No translations found:\n\n{}".format(contents))
        absolute_path = matches.group(1)
        
        logger.info("Removing {} from {}.po".format(absolute_path, domain))
        open(django_po, "w").write(contents.replace(absolute_path, ""))
        