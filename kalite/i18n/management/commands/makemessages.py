"""
Instead of re-writing the makemessages command built-in to Django, let's extend it here.
For now (11/12/15) we'll just deal with the existing output. In the future, we should revert makemessages to
vanilla Django and again do our custom actions *on top of* the vanilla output.
"""
import os
import polib
import yaml

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
]


class Command(makemessages.Command):

    def handle_noargs(self, *args, **options):
        # Set some sensible defaults
        for ignore_pattern in IGNORE_PATTERNS:
            if ignore_pattern not in options["ignore_patterns"]:
                options["ignore_patterns"].append(ignore_pattern)
        logging.debug("Ignoring the following patterns: {}".format(options["ignore_patterns"]))

        logging.debug("Calling base makemessages command.")
        super(Command, self).handle_noargs(*args, **options)
        lang_code = options["locale"]
        logging.debug("Modifying message catalog for locale '{}'".format(lang_code))

        # only add the inline help narratives for the JS catalog file.
        if options["domain"] == "djangojs":
            inline_help_poentries = self.extract_inline_help_strings()

            pofile_path = os.path.join(settings.USER_WRITABLE_LOCALE_DIR, lang_code, "LC_MESSAGES", "djangojs.po")
            po = polib.pofile(pofile_path)
            for entry in inline_help_poentries:
                po.append(entry)
            po.save(pofile_path)
