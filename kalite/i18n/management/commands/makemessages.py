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


IGNORE_PATTERNS = [
    "*/node_modules*",
    "*dist-packages*",
    "*python-packages*",
    "*/kalite/static*",
    "*bundle*.js",
    "*/ka-lite/build/*",
    "*/js/i18n/*.js",
    "*/ka-lite/docs/*"
]


class Command(makemessages.Command):

    def handle_noargs(self, *args, **options):
        # Set some sensible defaults
        for ignore_pattern in IGNORE_PATTERNS:
            if ignore_pattern not in options["ignore_patterns"]:
                options["ignore_patterns"].append(ignore_pattern)
        print("Ignoring the following patterns: {}".format(options["ignore_patterns"]))

        print("Calling base makemessages command.")
        super(Command, self).handle_noargs(*args, **options)

        narratives_file = os.path.join(settings.CONTENT_DATA_PATH, "narratives.yml")
        with open(narratives_file, "r") as f:
            raw_narrs = yaml.load(f)

        poentries = []
        for narr_key, targets in raw_narrs.iteritems():
            for target in targets:
                for target_name, steps in target.iteritems():
                    for step in steps:
                        for key, value in step.iteritems():
                            if key == "text":
                                poentries.append(polib.POEntry(
                                    msgid=value,
                                    msgstr="",
                                    occurrences=[(narratives_file, 0)]
                                ))

        lang_code = options["locale"]
        print("Modifying message catalog for locale '{}'".format(lang_code))
        pofile_path = os.path.join(settings.USER_WRITABLE_LOCALE_DIR, lang_code, "LC_MESSAGES", "django.po")
        po = polib.pofile(pofile_path)
        for entry in poentries:
            po.append(entry)
        po.save(pofile_path)
