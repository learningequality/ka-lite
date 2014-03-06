"""
CENTRAL SERVER ONLY

This command automates the process of generating template po files, which can be uploaded to crowdin.
It runs the django commands makemessages and compilemessages and moves the created files to an
exposed url, so that they can be downloaded from the web by KA's scripts.

It has an optional flag, -t, which inserts asterisks around the strings in the po files, and
compiles them, so that when you run the server, English has been translated to *English* in the
hope of making it easy to identify unwrapped strings.

This can be run independently of the "update_language_packs" command
"""
import glob
import re
import os
import shutil
from optparse import make_option

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

import settings
from i18n import lcode_to_django_dir, update_jsi18n_file
from settings import LOG as logging
from utils.django_utils import call_command_with_output
from utils.general import ensure_dir

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            '--test',
            '-t',
            dest='test_wrappings',
            action="store_true",
            default=False,
            help='Running with -t will fill in current po files msgstrs with asterisks. This will allow you to quickly identify unwrapped strings in the codebase and wrap them in translation tags! Remember to delete after your finished testing.',
        ),
    )
    help = 'USAGE: \'python manage.py update_po\' defaults to creating new template files. If run with -t, will generate test po files that make it easy to identify strings that need wrapping.'

    def handle(self, **options):
        if not settings.CENTRAL_SERVER and not options['test_wrappings']:
            raise CommandError("Wrappings should be run on the central server, and downloaded through languagepackdownload to the distributed server.")

        # All commands must be run from project root
        change_dir_to_project_root()

        # (safety measure) prevent any english or test translations from being uploaded
        delete_current_templates()

        # Create new files
        run_makemessages()

        # Handle flags
        if options["test_wrappings"]:
            generate_test_files()
            update_jsi18n_file()  # needed for test purposes only--regenerate the static js file
        else:
            update_templates()


def change_dir_to_project_root():
    """Change into the project root directory to run i18n commands"""
    logging.debug("Moving to project root directory")
    project_root = os.path.join(settings.PROJECT_PATH, "../")
    os.chdir(project_root)
    ensure_dir(os.path.join(project_root, "locale/"))


def delete_current_templates():
    """Delete existing en po/pot files"""
    logging.info("Deleting English language po files")
    for locale_path in settings.LOCALE_PATHS:
        english_path = os.path.join(locale_path, "en", "LC_MESSAGES")
        if os.path.exists(english_path):
            shutil.rmtree(english_path)

    logging.info("Deleting English language pot files")
    pot_path = os.path.join(settings.DATA_PATH, "i18n", "pot")
    if os.path.exists(pot_path):
        shutil.rmtree(pot_path)

    logging.info("Deleting old English language pot files")
    old_pot_path = os.path.join(settings.STATIC_ROOT, "pot")
    if os.path.exists(old_pot_path):
        shutil.rmtree(old_pot_path)

def run_makemessages():
    """Run makemessages command for english po files"""
    logging.info("Executing makemessages command")
    # Generate english po file
    ignore_pattern = ['python-packages/*'] + ['kalite/%s/*' % dirname for dirname in ['central', 'contact', 'faq', 'registration', 'tests', 'stats']]
    call_command('makemessages', locale='en', ignore_patterns=ignore_pattern, no_obsolete=True)
    # Generate english po file for javascript
    ignore_pattern = ['kalite/static/admin/js/*', 'python-packages/*', 'kalite/static/js/i18n/*', 'kalite/static/js/khan-exercises/*']
    call_command('makemessages', domain='djangojs', locale='en', ignore_patterns=ignore_pattern, no_obsolete=True)


def update_templates():
    """Update template po files"""
    pot_path = os.path.join(settings.DATA_PATH, "i18n", "pot")
    logging.info("Copying english po files to %s" % pot_path)

    #  post them to exposed URL
    ensure_dir(pot_path)
    shutil.copy(os.path.join(settings.LOCALE_PATHS[0], "en/LC_MESSAGES/django.po"), os.path.join(pot_path, "kalite.pot"))
    shutil.copy(os.path.join(settings.LOCALE_PATHS[0], "en/LC_MESSAGES/djangojs.po"), os.path.join(pot_path, "kalitejs.pot"))


def generate_test_files():
    """Insert asterisks as translations in po files"""

    # Open them up and insert asterisks for all empty msgstrs
    logging.info("Generating test po files")
    en_po_dir = os.path.join(settings.LOCALE_PATHS[0], "en/LC_MESSAGES/")
    for po_file in glob.glob(os.path.join(en_po_dir, "*.po")):

        msgid_pattern = re.compile(r'msgid \"(.*)\"\nmsgstr', re.S | re.M)

        content = open(os.path.join(en_po_dir, po_file), 'r').read()
        results = content.split("\n\n")
        with open(os.path.join(en_po_dir, "tmp.po"), 'w') as temp_file:
            # We know the first block is static, so just dump that.
            temp_file.write(results[0])

            # Now work through actual translations
            for result in results[1:]:
                try:
                    msgid = re.findall(msgid_pattern, result)[0]

                    temp_file.write("\n\n")
                    temp_file.write(result.replace("msgstr \"\"", "msgstr \"***%s***\"" % msgid))
                except Exception as e:
                    logging.error("Failed to insert test string: %s\n\n%s\n\n" % (e, result))

        # Once done replacing, rename temp file to overwrite original
        os.rename(os.path.join(en_po_dir, "tmp.po"), os.path.join(en_po_dir, po_file))

        (out, err, rc) = compile_po_files("en")
        if err:
            logging.debug("Error executing compilemessages: %s" % err)


def compile_po_files(lang_codes=None, failure_ok=True):
    """
    Compile all po files in locale directory.

    First argument (lang_codes) can be None (means all), a list/tuple, or even a string (shh...)
    """
    # before running compilemessages, ensure in correct directory
    change_dir_to_project_root()

    if not lang_codes or len(lang_codes) > 1:
        (out, err, rc) = call_command_with_output('compilemessages')
    else:
        lang_code = lang_codes if isinstance(lang_codes, basestring) else lang_codes[0]
        (out, err, rc) = call_command_with_output('compilemessages', locale=lcode_to_django_dir(lang_code))

    if err and not failure_ok:
        raise CommandError("Failure compiling po files: %s" % err)
    return out, err, rc
