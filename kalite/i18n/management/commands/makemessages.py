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
    "*dist-packages*",
    "*/LC_MESSAGES/*",
    "*python-packages*",
    "*/kalite/static*",
    "*bundle*.js",
    "*/ka-lite/build/*",
    "*/js/i18n/*.js",
    "*/ka-lite/docs/*",
    "*/ka-lite/data/*.yml",  #  we process the inline help docs separately
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

    def extract_inline_help_strings(self, inline_help_path=None):
        '''
        Extract the strings from the inline help narratives yml files. Returns an
        iterator containing the po file entries. Optional inline_help_parameter
        specifies where the inline help narratives path is. Else, it defaults
        to settings.CONTENT_DATA_PATH + "narratives.yml"

        '''
        narratives_file = inline_help_path or os.path.join(settings.CONTENT_DATA_PATH, "narratives.yml")
        with open(narratives_file, "r") as f:
            raw_narrs = yaml.load(f)

        for narr_key, targets in raw_narrs.iteritems():
            for target in targets:
                for target_name, steps in target.iteritems():
                    for step in steps:
                        for key, value in step.iteritems():
                            if key == "text":
                                yield polib.POEntry(
                                    msgid=value,
                                    msgstr="",
                                )
