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
"""
import datetime
import glob
import json
import os
import re
import requests
import shutil
import zipfile
import StringIO

from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.core.mail import mail_admins 

import settings
import version
from settings import LOG as logging
from shared.i18n import get_language_name, convert_language_code_format
from update_po import compile_all_po_files
from utils.general import ensure_dir, version_diff


LOCALE_ROOT = settings.LOCALE_PATHS[0]
LANGUAGE_PACK_AVAILABILITY_FILENAME = "language_pack_availability.json"

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
    )
    
    def handle(self, **options):
        if not settings.CENTRAL_SERVER:
            raise CommandError("This must only be run on the central server.")

        obliterate_old_schema()
        
        # Raw language code for srts
        update_srts(days=options["days"], lang_code=options["lang_code"])

        # Converted language code for language packs
        update_language_packs(lang_codes=[convert_language_code_format(options["lang_code"])] if options["lang_code"] != "all" else None)


def update_srts(days, lang_code):
    """
    Run the commands to update subtitles that haven't been updated in the number of days provided.
    Default is to update all srt files that haven't been requested in 30 days
    """
    date = '{0.month}/{0.day}/{0.year}'.format(datetime.date.today()-datetime.timedelta(int(days)))
    logging.info("Updating subtitles that haven't been refreshed since %s" % date)
    call_command("generate_subtitle_map", date_since_attempt=date)
    call_command("cache_subtitles", date_since_attempt=date, lang_code=lang_code)


def update_language_packs(lang_codes=None):

    ## Download latest UI translations from CrowdIn
    download_latest_translations() 
    
    ## Compile
    (out, err, rc) = compile_all_po_files()
    broken_langs = handle_po_compile_errors(lang_codes=lang_codes, out=out, err=err, rc=rc)

    ## Loop through new UI translations & subtitles, create/update unified meta data
    generate_metadata(lang_codes=lang_codes, broken_langs=broken_langs)
    
    ## Zip
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
            if lang != convert_language_code_format(lang):
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
    """Return list of languages to not rezip due to errors in compile process. Email admins errors"""

    broken_codes = re.findall(r'(?<=ka-lite/locale/)\w+(?=/LC_MESSAGES)', err)
    if lang_codes:
        broken_codes = list(set(broken_codes) - set(lang_codes))

    if broken_codes:
        logging.warning("Found %d errors while compiling in codes %s. Mailing admins report now."  % (len(broken_codes), ', '.join(broken_codes)))
        subject = "Error while compiling po files"
        commands = ""
        for code in broken_codes:
            commands += "\npython manage.py compilemessages -l %s" % code
        message =  """The following codes had errors when compiling their po files: %s.
                   Please rerun the following commands to see specific line numbers 
                   that need to be corrected on CrowdIn, before we can update the language packs.
                   %s""" % (', '.join(broken_codes), commands)
        if not settings.DEBUG:
            mail_admins(subject=subject, message=message)
            logging.info("Report sent.")
        else:
            logging.info("DEBUG is True so not sending email, but would have sent the following: SUBJECT: %s; MESSAGE: %s"  % (subject, message))
    return broken_codes


def download_latest_translations(project_id=settings.CROWDIN_PROJECT_ID, project_key=settings.CROWDIN_PROJECT_KEY, language_code="all"):
    """Download latest translations from CrowdIn to corresponding locale directory."""

    ## Build latest package
    build_translations()

    ## Get zip file of translations
    logging.info("Attempting to download a zip archive of current translations")
    request_url = "http://api.crowdin.net/api/project/%s/download/%s.zip?key=%s" % (project_id, language_code, project_key)
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

    ## Unpack into temp dir
    z = zipfile.ZipFile(StringIO.StringIO(r.content))
    tmp_dir_path = os.path.join(LOCALE_ROOT, "tmp")
    z.extractall(tmp_dir_path)

    ## Copy over new translations
    extract_new_po(tmp_dir_path, language_codes=[language_code] if language_code != "all" else None)

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


def extract_new_po(tmp_dir_path=os.path.join(LOCALE_ROOT, "tmp"), language_codes=[]):
    """Move newly downloaded po files to correct location in locale direction"""

    logging.info("Unpacking new translations")
    update_languages = os.listdir(tmp_dir_path)
    if language_codes:  # limit based on passed in limitations
        update_languages = set(update_languages).intersect(set(language_codes))

    for lang in update_languages:
        converted_code = convert_language_code_format(lang)
        # ensure directory exists in locale folder, and then overwrite local po files with new ones 
        ensure_dir(os.path.join(LOCALE_ROOT, converted_code, "LC_MESSAGES"))
        for po_file in glob.glob(os.path.join(tmp_dir_path, lang, "*/*.po")): 
            if "js" in os.path.basename(po_file):
                shutil.copy(po_file, os.path.join(LOCALE_ROOT, converted_code, "LC_MESSAGES", "djangojs.po"))
            else:
                shutil.copy(po_file, os.path.join(LOCALE_ROOT, converted_code, "LC_MESSAGES", "django.po"))


def generate_metadata(lang_codes=None, broken_langs=None):
    """Loop through locale folder, create or update language specific meta and create or update master file, skipping broken languages"""

    logging.info("Generating new po file metadata")
    master_file = []

    # loop through all languages in locale, update master file
    crowdin_meta_dict = get_crowdin_meta()
    subtitle_counts = json.loads(open(settings.SUBTITLES_DATA_ROOT + "subtitle_counts.json").read())
    for lang in os.listdir(LOCALE_ROOT):
        # skips anything not a directory
        if not os.path.isdir(os.path.join(LOCALE_ROOT, lang)):
            logging.info("Skipping %s because it is not a directory" % lang)
            continue
        elif lang in broken_langs:
            logging.info("Skipping %s because it triggered an error during compilemessages. The admins should have received a report about this and must fix it before this pack will be updateed." % lang)
            continue
        crowdin_meta = next((meta for meta in crowdin_meta_dict if meta["code"] == convert_language_code_format(lang_code=lang, for_crowdin=True)), None)
        try:
            local_meta = json.loads(open(os.path.join(LOCALE_ROOT, lang, "%s_metadata.json" % lang)).read())
        except:
            local_meta = {}
        if not crowdin_meta:
            converted_lang_code = convert_language_code_format(lang)
            updated_meta = {
                "code": converted_lang_code,
                "name": get_language_name(converted_lang_code),
                "percent_translated": 0,
                "phrases": 0,
                "approved_translations": 0,
            }
        else:
            updated_meta = {
                "code": crowdin_meta.get("code"),
                "name": crowdin_meta.get("name"),
                "percent_translated": int(crowdin_meta.get("approved_progress")),
                "phrases": int(crowdin_meta.get("phrases")),
                "approved_translations": int(crowdin_meta.get("approved")),
            }

        # Obtain current number of subtitles
        entry = subtitle_counts.get(get_language_name(lang))
        if entry:
            srt_count = entry.get("count")
        else:
            srt_count = 0

        updated_meta.update({
            "software_version": version.VERSION,
            "subtitle_count": srt_count,
        })

        language_pack_version = increment_language_pack_version(local_meta, updated_meta)
        updated_meta["language_pack_version"] = language_pack_version
        local_meta.update(updated_meta)

        # Write locally (this is used on download by distributed server to update it's database)
        with open(os.path.join(LOCALE_ROOT, lang, "%s_metadata.json" % lang), 'w') as output:
            json.dump(local_meta, output)
        
        # Update master (this is used for central server to handle API requests for data)
        master_file.append(local_meta)

    # Save updated master
    ensure_dir(settings.LANGUAGE_PACK_ROOT)
    with open(os.path.join(settings.LANGUAGE_PACK_ROOT, LANGUAGE_PACK_AVAILABILITY_FILENAME), 'w') as output:
        json.dump(master_file, output) 
    logging.info("Local record of translations updated")


def get_crowdin_meta(project_id=settings.CROWDIN_PROJECT_ID, project_key=settings.CROWDIN_PROJECT_KEY):
    """Return tuple in format (total_strings, total_translated, percent_translated)"""

    request_url = "http://api.crowdin.net/api/project/%s/status?key=%s&json=True" % (project_id, project_key)
    r = requests.get(request_url)
    r.raise_for_status()

    crowdin_meta_dict = json.loads(r.content)
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
    """Zip up and expose all language packs"""

    lang_codes = lang_codes or listdir(LOCALE_ROOT)
    logging.info("Zipping up %d language pack(s)" % len(lang_codes))

    ensure_dir(settings.LANGUAGE_PACK_ROOT)
    for lang in lang_codes:
        lang_locale_path = os.path.join(LOCALE_ROOT, lang)

        if not os.path.exists(lang_locale_path):
            logging.warn("Unexpectedly skipping missing directory: %s" % lang)
        elif not os.path.isdir(lang_locale_path):
            logging.error("Skipping language where a file exists: %s" % lang)

        # Create a zipfile for this language
        zip_path = os.path.join(settings.LANGUAGE_PACK_ROOT, version.VERSION)
        ensure_dir(zip_path)
        z = zipfile.ZipFile(os.path.join(zip_path, "%s.zip" % convert_language_code_format(lang)), 'w')

        # Get every single file in the directory and zip it up
        for metadata_file in glob.glob('%s/*.json' % lang_locale_path):
            z.write(os.path.join(lang_locale_path, metadata_file), arcname=os.path.basename(metadata_file))    
        for mo_file in glob.glob('%s/LC_MESSAGES/*.mo' % lang_locale_path):
            z.write(os.path.join(lang_locale_path, mo_file), arcname=os.path.join("LC_MESSAGES", os.path.basename(mo_file)))
        for srt_file in glob.glob('%s/subtitles/*.srt' % lang_locale_path):
            z.write(os.path.join(lang_locale_path, srt_file), arcname=os.path.join("subtitles", os.path.basename(srt_file)))
        z.close()
    logging.info("Done.")