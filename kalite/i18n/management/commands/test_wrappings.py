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
import sys
from optparse import make_option

from django.conf import settings; logging = settings.LOG
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from ... import LOCALE_ROOT, get_po_filepath, lcode_to_django_dir, update_jsi18n_file
from fle_utils.django_utils import call_command_with_output
from fle_utils.general import ensure_dir


PROJECT_ROOT = os.path.join(settings.PROJECT_PATH, "../")

class Command(BaseCommand):

    def handle(self, **options):

        delete_current_templates()

        # Create new files
        run_makemessages(verbosity=options["verbosity"])

        # Handle flags
        generate_test_files()
        update_jsi18n_file()  # needed for test purposes only--regenerate the static js file


def delete_current_templates():
    """Delete existing en po/pot files"""
    logging.info("Deleting English language po files")
    for locale_path in settings.LOCALE_PATHS:
        english_path = get_po_filepath("en")
        if os.path.exists(english_path):
            shutil.rmtree(english_path)


def run_makemessages(ignore_patterns_py=[], ignore_patterns_js=[], verbosity=0):
    """Run makemessages command for english po files"""

    # Do some packages only
    python_package_dirs = glob.glob(os.path.join(PROJECT_ROOT, 'python-packages', '*'))
    ignored_packages = [os.path.join('*/python-packages/', os.path.basename(pp)) for pp in python_package_dirs if os.path.basename(pp) not in ['securesync', 'fle_utils']]

    # Besides externally requested ignores, add on a few standard ones.
    ignore_shared = ignored_packages + ['*/data/*', '*/.git/*', '*/migrations/*', '*/node_modules/*', '*/fle_utils/chronograph/*']
    ignore_patterns_py = ignore_patterns_py + ignore_shared + ['*/static-libraries/*']
    ignore_patterns_js = ignore_patterns_js + ignore_shared + ['*/kalite/static/*', '*/static-libraries/admin/*', '*/static-libraries/js/i18n/*', '*/kalite/distributed/static/khan-exercises/*'] + ['*jquery*', '*bootstrap*']

    logging.debug("Creating / validating locale root folder")
    ensure_dir(LOCALE_ROOT)

    # Command must be run from project root
    logging.debug("Moving to project root directory")
    os.chdir(PROJECT_ROOT)

    call_command('clean_pyc', path=PROJECT_ROOT)

    logging.info("Executing makemessages command")
    # Generate english po file
    sys.stdout.write("\n\nCompiling .py / .html files... ")
    call_command('makemessages', extensions=['html', 'py'], verbosity=verbosity, locale='en', ignore_patterns=ignore_patterns_py, no_obsolete=True)

    # Generate english po file for javascript
    sys.stdout.write("\n\nCompiling .js files... ")
    call_command('makemessages', extensions=['js'], domain='djangojs', verbosity=verbosity, locale='en', ignore_patterns=ignore_patterns_js, no_obsolete=True)


def generate_test_files():
    """Insert asterisks as translations in po files"""

    # Open them up and insert asterisks for all empty msgstrs
    logging.info("Generating test po files")
    for po_file in glob.glob(get_po_filepath(lang_code="en", filename="*.po")):

        msgid_pattern = re.compile(r'msgid \"(.*)\"\nmsgstr', re.S | re.M)

        content = open(get_po_filepath(lang_code="en", filename=po_file), 'r').read()
        results = content.split("\n\n")
        with open(get_po_filepath(lang_code="en", filename="tmp.po"), 'w') as temp_file:
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
        os.rename(get_po_filepath(lang_code="en", filename="tmp.po"), get_po_filepath(lang_code="en", filename=po_file))

        (out, err, rc) = compile_po_files("en")
        if err:
            logging.debug("Error executing compilemessages: %s" % err)


def compile_po_files(lang_codes=None, failure_ok=True):
    """
    Compile all po files in locale directory.

    First argument (lang_codes) can be None (means all), a list/tuple, or even a string (shh...)
    """
    # before running compilemessages, ensure in correct directory
    logging.debug("Moving to project root directory")
    os.chdir(PROJECT_ROOT)


    if not lang_codes or len(lang_codes) > 1:
        (out, err, rc) = call_command_with_output('compilemessages')
    else:
        lang_code = lang_codes if isinstance(lang_codes, basestring) else lang_codes[0]
        (out, err, rc) = call_command_with_output('compilemessages', locale=lcode_to_django_dir(lang_code))

    if err and not failure_ok:
        raise CommandError("Failure compiling po files: %s" % err)
    return out, err, rc
