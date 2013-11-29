"""
This command is the master command for language packs. Based on
command line arguments provided, it calls all i18n commands
necessary to update language packs.

1. Updates all cached srt files  from Amara
2. Downloads latest translations from CrowdIn
3. Generates metadata on language packs (subtitles and UI translations)
4. Compiles the UI translations
5. Zips up the packs and exposes them at a static url

Good test cases:

./manage.py -l aa # language with subtitles, no translations
./manage.py -l ur-PK # language with translations, no subtitles

NOTE: all language codes internally are assumed to be in django format (e.g. en_US)
"""
import datetime
import glob
import json
import os
import re
import requests
import shutil
import tempfile
import zipfile
import StringIO

from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.core.mail import mail_admins

import settings
import version
from settings import LOG as logging
from shared.i18n import LANGUAGE_PACK_AVAILABILITY_FILEPATH, LOCALE_ROOT, SUBTITLES_DATA_ROOT, SUBTITLE_COUNTS_FILEPATH
from shared.i18n import get_language_name, lcode_to_django, lcode_to_ietf, LanguageNotFoundError, get_language_pack_metadata_filepath, get_language_pack_filepath
from update_po import compile_po_files
from utils.general import ensure_dir, version_diff


class Command(BaseCommand):
    help = 'Updates all language packs'

    option_list = BaseCommand.option_list + (
        make_option('-d', '--days',
                    action='store',
                    dest='days',
                    default=0 if not settings.DEBUG else 365,
                    metavar="NUM_DAYS",
                    help="Update any and all subtitles that haven't been refreshed in the numebr of days given. Defaults to 0 days."),
        make_option('-l', '--lang_code',
                    action='store',
                    dest='lang_code',
                    default="all",
                    metavar="LANG_CODE",
                    help="Language code to update (default: all)"),
        make_option('--no_ka',
                    action='store_true',
                    dest='no_ka',
                    default=False,
                    help='Do not include Khan Academy content translations.'),
        make_option('--zip_file',
                    action='store',
                    dest='zip_file',
                    default=None,
                    help='a local zip file to be used instead of fetching to CrowdIn. Ignores -l if this is used.'),
        make_option('--ka_zip_file',
                    action='store',
                    dest='ka_zip_file',
                    default=None,
                    help='a local zip file to be used for KA content instead of fetching to CrowdIn. Ignores -l if this is used.'),
    )

    def handle(self, **options):
        if not settings.CENTRAL_SERVER:
            raise CommandError("This must only be run on the central server.")
        if not options["lang_code"] or options["lang_code"].lower() == "all":
            lang_codes = None
        else:
            lang_codes = [lcode_to_django(lc) for lc in options["lang_code"].split(",")]

        obliterate_old_schema()

        # Raw language code for srts
        update_srts(days=options["days"], lang_codes=lang_codes)

        # Converted language code for language packs
        update_language_packs(
            lang_codes=lang_codes,
            zip_file=options['zip_file'],
            ka_zip_file=options['ka_zip_file'],
            download_ka_translations=not options['no_ka'],
        )


def update_srts(days, lang_codes):
    """
    Run the commands to update subtitles that haven't been updated in the number of days provided.
    Default is to update all srt files that haven't been requested in 30 days
    """
    date = '{0.month}/{0.day}/{0.year}'.format(datetime.date.today() - datetime.timedelta(int(days)))
    logging.info("Updating subtitles that haven't been refreshed since %s" % date)
    call_command("generate_subtitle_map", date_since_attempt=date)
    for lang_code in lang_codes:
        call_command("cache_subtitles", date_since_attempt=date, lang_code=lang_code)


def update_language_packs(lang_codes=None, download_ka_translations=True, zip_file=None, ka_zip_file=None):

    logging.info("Downloading %s language(s)" % lang_codes)

    # Download latest UI translations from CrowdIn
    assert hasattr(settings, "CROWDIN_PROJECT_ID") and hasattr(settings, "CROWDIN_PROJECT_KEY"), "Crowdin keys must be set to do this."

    for lang_code in (lang_codes or [None]):
        download_latest_translations(
            lang_code=lang_code,
            project_id=settings.CROWDIN_PROJECT_ID,
            project_key=settings.CROWDIN_PROJECT_KEY,
            zip_file=zip_file,
        )

        # Download Khan Academy translations too
        if download_ka_translations:
            assert hasattr(settings, "KA_CROWDIN_PROJECT_ID") and hasattr(settings, "KA_CROWDIN_PROJECT_KEY"), "KA Crowdin keys must be set to do this."

            logging.info("Downloading Khan Academy translations...")
            download_latest_translations(
                lang_code=lang_code,
                project_id=settings.KA_CROWDIN_PROJECT_ID,
                project_key=settings.KA_CROWDIN_PROJECT_KEY,
                zip_file=ka_zip_file,
                rebuild=False,  # just to be friendly to KA--we shouldn't force a rebuild
            )

    # Compile
    (out, err, rc) = compile_po_files(lang_codes=lang_codes)  # converts to django
    broken_langs = handle_po_compile_errors(lang_codes=lang_codes, out=out, err=err, rc=rc)

    # Loop through new UI translations & subtitles, create/update unified meta data
    generate_metadata(lang_codes=lang_codes, broken_langs=broken_langs)

    # Zip
    zip_language_packs(lang_codes=lang_codes)


def obliterate_old_schema():
    """Move srt files from static/srt to locale directory and file them by language code, delete any old locale directories"""
    srt_root = os.path.join(settings.STATIC_ROOT, "srt")


    for locale_root in settings.LOCALE_PATHS:
        if not os.path.exists(locale_root):
            continue
        for lang in os.listdir(locale_root):
            # Skips if not a directory
            if not os.path.isdir(os.path.join(locale_root, lang)):
                continue
            # If it isn't crowdin/django format, keeeeeeellllllll
            if lang != lcode_to_django(lang):
                logging.info("Deleting %s directory because it does not fit our language code format standards" % lang)
                shutil.rmtree(os.path.join(locale_root, lang))

    if os.path.exists(os.path.join(settings.STATIC_ROOT, "srt")):
        logging.info("Outdated schema detected for storing srt files. Hang tight, the moving crew is on it.")
        for lang in os.listdir(srt_root):
            # Skips if not a directory
            if not os.path.isdir(os.path.join(srt_root, lang)):
                continue
            lang_srt_path = os.path.join(srt_root, lang, "subtitles/")
            lang_locale_path = os.path.join(locale_root, lang)
            ensure_dir(lang_locale_path)
            dst = os.path.join(lang_locale_path, "subtitles")

            for srt_file_path in glob.glob(os.path.join(lang_srt_path, "*.srt")):
                base_path, srt_filename = os.path.split(srt_file_path)
                if not os.path.exists(os.path.join(dst, srt_filename)):
                    ensure_dir(dst)
                    shutil.move(srt_file_path, os.path.join(dst, srt_filename))

        shutil.rmtree(srt_root)
        logging.info("Move completed.")

def handle_po_compile_errors(lang_codes=None, out=None, err=None, rc=None):
    """
    Return list of languages to not rezip due to errors in compile process.
    Then email admins errors.
    """

    broken_codes = re.findall(r'(?<=ka-lite/locale/)\w+(?=/LC_MESSAGES)', err) or []

    if lang_codes:
        # Only show the errors relevant to the list of language codes passed in.
        lang_codes = set([lcode_to_django(lc) for lc in lang_codes])
        broken_codes = list(set(broken_codes).intersection(lang_codes))

    if broken_codes:
        logging.warning("Found %d errors while compiling in codes %s. Mailing admins report now."  % (len(broken_codes), ', '.join(broken_codes)))
        subject = "Error while compiling po files"
        commands = "\n".join(["python manage.py compilemessages -l %s" % lc for lc in broken_codes])
        message =  """The following codes had errors when compiling their po files: %s.
                   Please rerun the following commands to see specific line numbers
                   that need to be corrected on CrowdIn, before we can update the language packs.
                   %s""" % (
            ', '.join([lcode_to_ietf(lc) for lc in broken_codes]),
            commands,
        )
        if not settings.DEBUG:
            mail_admins(subject=subject, message=message)
            logging.info("Report sent.")
        else:
            logging.info("DEBUG is True so not sending email, but would have sent the following: SUBJECT: %s; MESSAGE: %s"  % (subject, message))

    return broken_codes


def download_latest_translations(project_id=settings.CROWDIN_PROJECT_ID,
                                 project_key=settings.CROWDIN_PROJECT_KEY,
                                 lang_code="all",
                                 zip_file=None,
                                 rebuild=True):
    """
    Download latest translations from CrowdIn to corresponding locale
    directory. If zip_file is given, use that as the zip file
    instead of going through CrowdIn.

    """
    # Get zip file of translations
    if zip_file and os.path.exists(zip_file):
        logging.info("Using local zip file at %s" % zip_file)
        z = zipfile.ZipFile(zip_file)
        # use the name of the zip file to infer the language code, if needed
        lang_code = lang_code or os.path.splitext(os.path.basename(zip_file))[0]

    else:
        # Tell CrowdIn to Build latest package
        if rebuild:
            build_translations()

        logging.info("Attempting to download a zip archive of current translations")
        request_url = "http://api.crowdin.net/api/project/%s/download/%s.zip?key=%s" % (project_id, lang_code, project_key)
        r = requests.get(request_url)
        try:
            r.raise_for_status()
        except Exception as e:
            if r.status_code == 401:
                raise CommandError("Error: 401 Unauthorized while trying to access the CrowdIn API. Be sure to set CROWDIN_PROJECT_ID and CROWDIN_PROJECT_KEY in local_settings.py.")
            else:
                raise CommandError("Error: %s - couldn't connect to CrowdIn API - cannot continue without that zip file!" % e)
        else:
            logging.info("Successfully downloaded zip archive")

        # Unpack into temp dir
        z = zipfile.ZipFile(StringIO.StringIO(r.content))

        if zip_file:
            with open(zip_file, "wb") as fp:  # save the zip file
                fp.write(r.content)

    tmp_dir_path = tempfile.mkdtemp()
    z.extractall(tmp_dir_path)

    # Copy over new translations
    extract_new_po(tmp_dir_path, lang_codes=[lang_code] if lang_code != "all" else None)

    # Clean up tracks
    if os.path.exists(tmp_dir_path):
        shutil.rmtree(tmp_dir_path)


def build_translations(project_id=settings.CROWDIN_PROJECT_ID, project_key=settings.CROWDIN_PROJECT_KEY):
    """Build latest translations into zip archive on CrowdIn"""

    logging.info("Requesting that CrowdIn build a fresh zip of our translations")
    request_url = "http://api.crowdin.net/api/project/%s/export?key=%s" % (project_id, project_key)
    r = requests.get(request_url)
    try:
        r.raise_for_status()
    except Exception as e:
        logging.error(e)


def extract_new_po(tmp_dir_path=None, lang_codes=[]):
    """Move newly downloaded po files to correct location in locale direction"""

    if not tmp_dir_path:
        tmp_dir_path = tempfile.mkdtemp()

    logging.info("Unpacking new translations")
    update_languages = os.listdir(tmp_dir_path)
    if lang_codes:  # limit based on passed in limitations
        update_languages = set(update_languages).intersection(set(lang_codes))

    for lang in update_languages:
        converted_code = lcode_to_django(lang)
        # ensure directory exists in locale folder, and then overwrite local po files with new ones
        ensure_dir(os.path.join(LOCALE_ROOT, converted_code, "LC_MESSAGES"))
        for po_file in glob.glob(os.path.join(tmp_dir_path, lang, "*/*.po")):
            if "js" in os.path.basename(po_file):
                shutil.copy(po_file, os.path.join(LOCALE_ROOT, converted_code, "LC_MESSAGES", "djangojs.po"))
            else:
                shutil.copy(po_file, os.path.join(LOCALE_ROOT, converted_code, "LC_MESSAGES", "django.po"))


def generate_metadata(lang_codes=None, broken_langs=None):
    """
    Loop through locale folder, create or update language specific meta and create or update master file, skipping broken languages

    note: broken_langs must be in django format.
    """
    logging.info("Generating new language pack metadata")

    lang_codes = lang_codes or os.listdir(LOCALE_ROOT)
    try:
        with open(LANGUAGE_PACK_AVAILABILITY_FILEPATH, "r") as fp:
            master_metadata = json.load(fp)
    except Exception as e:
        logging.warn("Error opening language pack metadata: %s; resetting" % e)
        master_metadata = []

    # loop through all languages in locale, update master file
    crowdin_meta_dict = download_crowdin_metadata()
    with open(SUBTITLE_COUNTS_FILEPATH, "r") as fp:
        subtitle_counts = json.load(fp)

    for lc in lang_codes:
        lang_code_django = lcode_to_django(lc)
        lang_code_ietf = lcode_to_ietf(lc)
        lang_name = get_language_name(lang_code_ietf)

        # skips anything not a directory, or with errors
        if not os.path.isdir(os.path.join(LOCALE_ROOT, lang_code_django)):
            logging.info("Skipping item %s because it is not a directory" % lang_code_django)
            continue
        elif lang_code_django in broken_langs:  # broken_langs is django format
            logging.info("Skipping directory %s because it triggered an error during compilemessages. The admins should have received a report about this and must fix it before this pack will be updateed." % lang_code_django)
            continue

        # Gather existing metadata
        crowdin_meta = next((meta for meta in crowdin_meta_dict if meta["code"] == lang_code_ietf), {})
        metadata_filepath = get_language_pack_metadata_filepath(lang_code_ietf)
        try:
            with open(metadata_filepath) as fp:
                local_meta = json.load(fp)
        except:
            local_meta = {}

        try:
            # update metadata
            updated_meta = {
                "code": lcode_to_ietf(crowdin_meta.get("code") or lang_code_django),  # user-facing code
                "name": crowdin_meta.get("name") or lang_name,
                "percent_translated": int(crowdin_meta.get("approved_progress", 0)),
                "phrases": int(crowdin_meta.get("phrases", 0)),
                "approved_translations": int(crowdin_meta.get("approved", 0)),
            }

            # Obtain current number of subtitles
            entry = subtitle_counts.get(lang_name, {})
            srt_count = entry.get("count", 0)

            updated_meta.update({
                "software_version": version.VERSION,
                "subtitle_count": srt_count,
            })

        except LanguageNotFoundError:
            logging.error("Unrecognized language; must skip item %s" % lang_code_django)
            continue

        language_pack_version = increment_language_pack_version(local_meta, updated_meta)
        updated_meta["language_pack_version"] = language_pack_version
        local_meta.update(updated_meta)

        # Write locally (this is used on download by distributed server to update it's database)
        with open(metadata_filepath, 'w') as output:
            json.dump(local_meta, output)

        # Update master (this is used for central server to handle API requests for data)
        master_metadata.append(local_meta)

    # Save updated master
    ensure_dir(os.path.dirname(LANGUAGE_PACK_AVAILABILITY_FILEPATH))
    with open(LANGUAGE_PACK_AVAILABILITY_FILEPATH, 'w') as output:
        json.dump(master_metadata, output)
    logging.info("Local record of translations updated")


def download_crowdin_metadata(project_id=settings.CROWDIN_PROJECT_ID, project_key=settings.CROWDIN_PROJECT_KEY):
    """Return tuple in format (total_strings, total_translated, percent_translated)"""

    request_url = "http://api.crowdin.net/api/project/%s/status?key=%s&json=True" % (project_id, project_key)
    resp = requests.get(request_url)
    resp.raise_for_status()

    crowdin_meta_dict = json.loads(resp.content)
    return crowdin_meta_dict


def increment_language_pack_version(local_meta, updated_meta):
    """Increment language pack version if translations have been updated (start over if software version has incremented)"""
    if not local_meta or version_diff(local_meta.get("software_version"), version.VERSION) < 0:
        # set to one for the first time, or if this is the first build of a new software version
        language_pack_version = 1
    elif local_meta.get("total_translated") == updated_meta.get("approved") and local_meta.get("subtitle_count") == updated_meta.get("subtitle_count"):
        language_pack_version = local_meta.get("language_pack_version") or 1
    else:
        language_pack_version = local_meta.get("language_pack_version") + 1
    return language_pack_version



def zip_language_packs(lang_codes=None):
    """Zip up and expose all language packs

    converts all into ietf
    """

    lang_codes = lang_codes or listdir(LOCALE_ROOT)
    lang_codes = [lcode_to_ietf(lc) for lc in lang_codes]
    logging.info("Zipping up %d language pack(s)" % len(lang_codes))

    for lang_code_ietf in lang_codes:
        lang_code_django = lcode_to_django(lang_code_ietf)
        lang_locale_path = os.path.join(LOCALE_ROOT, lang_code_django)

        if not os.path.exists(lang_locale_path):
            logging.warn("Unexpectedly skipping missing directory: %s" % lang_code_django)
        elif not os.path.isdir(lang_locale_path):
            logging.error("Skipping language where a file exists where a directory was expected: %s" % lang_code_django)

        # Create a zipfile for this language
        zip_filepath = get_language_pack_filepath(lang_code_ietf)
        ensure_dir(os.path.dirname(zip_filepath))
        z = zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED)

        # Get every single file in the directory and zip it up
        for metadata_file in glob.glob('%s/*.json' % lang_locale_path):
            z.write(os.path.join(lang_locale_path, metadata_file), arcname=os.path.basename(metadata_file))
        for mo_file in glob.glob('%s/LC_MESSAGES/*.mo' % lang_locale_path):
            z.write(os.path.join(lang_locale_path, mo_file), arcname=os.path.join("LC_MESSAGES", os.path.basename(mo_file)))
        for srt_file in glob.glob('%s/subtitles/*.srt' % lang_locale_path):
            z.write(os.path.join(lang_locale_path, srt_file), arcname=os.path.join("subtitles", os.path.basename(srt_file)))
        z.close()
    logging.info("Done.")
