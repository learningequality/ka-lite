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
import fnmatch
import gc
import glob
import json
import os
import polib
import re
import requests
import shutil
import subprocess
import sys
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
from shared.i18n import LOCALE_ROOT, SUBTITLE_COUNTS_FILEPATH, CROWDIN_CACHE_DIR, DUBBED_VIDEOS_MAPPING_FILEPATH
from shared.i18n import get_language_name, lcode_to_django_dir, lcode_to_ietf, LanguageNotFoundError, get_dubbed_video_map,  get_localized_exercise_dirpath, get_language_pack_metadata_filepath, get_language_pack_availability_filepath, get_language_pack_filepath, move_old_subtitles, scrub_locale_paths, get_subtitle_count, get_localized_exercise_count
from update_po import compile_po_files
from utils.general import ensure_dir, softload_json, version_diff


# Attributes whose value, if changed, should change the version of the language pack.
VERSION_CHANGING_ATTRIBUTES = ["approved_translations", "phrases", "subtitle_count", "num_dubbed_videos", "num_exercises"]

class Command(BaseCommand):
    help = 'Updates all language packs'

    option_list = BaseCommand.option_list + (
        make_option('-d', '--days',
                    action='store',
                    dest='days',
                    default=1 if not settings.DEBUG else 365,
                    metavar="NUM_DAYS",
                    help="Update any and all subtitles that haven't been refreshed in the numebr of days given. Defaults to 0 days."),
        make_option('-l', '--lang_code',
                    action='store',
                    dest='lang_code',
                    default="all",
                    metavar="LANG_CODE",
                    help="Language code to update (default: all)"),
        make_option('--no-srts',
                    action='store_true',
                    dest='no_srts',
                    default=False,
                    help='Do not refresh video subtitles before bundling.'),
        make_option('--no-kalite-trans',
                    action='store_true',
                    dest='no_kalite_trans',
                    default=True,
                    help='Do not refresh KA Lite content translations before bundling.'),
        make_option('--no-ka-trans',
                    action='store_true',
                    dest='no_ka_trans',
                    default=False,
                    help='Do not refresh Khan Academy content translations before bundling.'),
        make_option('--no-exercises',
                    action='store_true',
                    dest='no_exercises',
                    default=False,
                    help='Do not refresh Khan Academy exercises before bundling.'),
        make_option('--no-dubbed',
                    action='store_true',
                    dest='no_dubbed',
                    default=False,
                    help='Do not refresh Khan Academy dubbed video mappings.'),
        make_option('--no-update',
                    action='store_true',
                    dest='no_update',
                    default=False,
                    help='Do not refresh any resources before packaging.'),
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
        make_option('-o', '--use_local',
                    action='store_true',
                    dest='use_local',
                    default=False,
                    metavar="USE_LOCAL",
                    help="Use the local po files, instead of refreshing from online (a way to test translation tweaks)"),
    )

    def handle(self, *args, **options):
        if not settings.CENTRAL_SERVER:
            raise CommandError("This must only be run on the central server.")
        if not options["lang_code"] or options["lang_code"].lower() == "all":
            lang_codes = ['all']
        else:
            lang_codes = [lcode_to_ietf(lc) for lc in options["lang_code"].split(",")]

        upgrade_old_schema()

        package_metadata = dict([(lang_code, {}) for lang_code in lang_codes])

        # Update all the latest srts
        if not options['no_srts'] and not options['no_update']:
            update_srts(days=options["days"], lang_codes=lang_codes)
        for lang_code in lang_codes:
            package_metadata[lang_code]["subtitle_count"] = get_subtitle_count(lang_code)

        # Update the dubbed video mappings
        if not options['no_dubbed'] and not options['no_update']:
            get_dubbed_video_map(force=True)
        for lang_code in lang_codes:
            dv_map = get_dubbed_video_map(lang_code)
            package_metadata[lang_code]["num_dubbed_videos"] = len(dv_map) if dv_map else 0

        # Update the exercises
        for lang_code in lang_codes:
            if not options['no_exercises'] and not options['no_update']:
                call_command("scrape_exercises", lang_code=lang_code)
            package_metadata[lang_code]["num_exercises"] = get_localized_exercise_count(lang_code)

        # Update the crowdin translations
        (trans_metadata, broken_langs) = update_translations(
            lang_codes=lang_codes,
            zip_file=options['zip_file'],
            ka_zip_file=options['ka_zip_file'],
            download_ka_translations=not options['no_ka_trans'] and not options['no_update'],
            download_kalite_translations=not options['no_kalite_trans'] and not options['no_update'],
            use_local=options["use_local"],
        )
        for lang_code in lang_codes:
            package_metadata[lang_code].update(trans_metadata.get(lang_code, {}))

        # Loop through new UI translations & subtitles, create/update unified meta data
        generate_metadata(lang_codes=lang_codes, broken_langs=broken_langs, package_metadata=package_metadata)

        # Zip
        package_sizes = zip_language_packs(lang_codes=lang_codes)
        logging.debug("Package sizes: %s" % package_sizes)

        # Loop through new UI translations & subtitles, create/update unified meta data
        update_metadata(package_sizes)


def update_srts(days, lang_codes):
    """
    Run the commands to update subtitles that haven't been updated in the number of days provided.
    Default is to update all srt files that haven't been requested in 30 days
    """
    date = '{0.month}/{0.day}/{0.year}'.format(datetime.date.today() - datetime.timedelta(int(days)))
    logging.info("Updating subtitles that haven't been refreshed since %s" % date)
    call_command("generate_subtitle_map", date_since_attempt=date)
    if lang_codes:
        for lang_code in lang_codes:
            call_command("cache_subtitles", date_since_attempt=date, lang_code=lang_code)
    else:
        call_command("cache_subtitles", date_since_attempt=date)


def update_translations(lang_codes=None,
                        download_kalite_translations=True,
                        download_ka_translations=True,
                        zip_file=None,
                        ka_zip_file=None,
                        use_local=False):

    package_metadata = {}

    if use_local:
        for lang_code in lang_codes:
            lang_code = lcode_to_ietf(lang_code)
            package_metadata[lang_code] = {}
            combined_po_file = os.path.join(LOCALE_ROOT, lcode_to_django_dir(lang_code), "LC_MESSAGES", "django.po")
            ka_metadata = get_po_metadata(combined_po_file)
            package_metadata[lang_code]["approved_translations"] = ka_metadata["approved_translations"]
            package_metadata[lang_code]["phrases"]               = ka_metadata["phrases"]

    else:
        logging.info("Downloading %s language(s)" % lang_codes)

        # Download latest UI translations from CrowdIn


        # Download Khan Academy translations too
        if download_ka_translations:
            assert hasattr(settings, "KA_CROWDIN_PROJECT_ID") and hasattr(settings, "KA_CROWDIN_PROJECT_KEY"), "KA Crowdin keys must be set to do this."

        for lang_code in (lang_codes or [None]):
            lang_code = lcode_to_ietf(lang_code)

            package_metadata[lang_code] = {
                'approved_translations': 0,
                'phrases': 0,
                'kalite_ntranslations': 0,
                'kalite_nphrases': 0,
            }                   # these values will likely yield the wrong values when download_kalite_translations == False.

            kalite_po_file = None

            if download_kalite_translations:
                assert hasattr(settings, "CROWDIN_PROJECT_ID") and hasattr(settings, "CROWDIN_PROJECT_KEY"), "Crowdin keys must be set to do this."

                logging.info("Downloading KA Lite translations...")
                kalite_po_file = download_latest_translations(
                    lang_code=lang_code,
                    project_id=settings.CROWDIN_PROJECT_ID,
                    project_key=settings.CROWDIN_PROJECT_KEY,
                    zip_file=zip_file or (os.path.join(CROWDIN_CACHE_DIR, "kalite-%s.zip" % lang_code) if settings.DEBUG else None),
                )
                kalite_metadata = get_po_metadata(kalite_po_file)
                package_metadata[lang_code]["approved_translations"] = kalite_metadata["approved_translations"]
                package_metadata[lang_code]["phrases"]               = kalite_metadata["phrases"]
                package_metadata[lang_code]["kalite_ntranslations"]  = kalite_metadata["approved_translations"]
                package_metadata[lang_code]["kalite_nphrases"]       = kalite_metadata["phrases"]

            # Download Khan Academy translations too
            if download_ka_translations:
                assert hasattr(settings, "KA_CROWDIN_PROJECT_ID") and hasattr(settings, "KA_CROWDIN_PROJECT_KEY"), "KA Crowdin keys must be set to do this."

                logging.info("Downloading Khan Academy translations...")
                combined_po_file = download_latest_translations(
                    lang_code=lang_code,
                    project_id=settings.KA_CROWDIN_PROJECT_ID,
                    project_key=settings.KA_CROWDIN_PROJECT_KEY,
                    zip_file=ka_zip_file or (os.path.join(CROWDIN_CACHE_DIR, "ka-%s.zip" % lang_code) if settings.DEBUG else None),
                    combine_with_po_file=kalite_po_file,
                    rebuild=False,  # just to be friendly to KA--we shouldn't force a rebuild
                    download_type="ka",
                )
                ka_metadata = get_po_metadata(combined_po_file)
                package_metadata[lang_code]["approved_translations"] = ka_metadata["approved_translations"]
                package_metadata[lang_code]["phrases"]               = ka_metadata["phrases"]
                package_metadata[lang_code]["ka_ntranslations"]      = ka_metadata["approved_translations"] - package_metadata[lang_code]["kalite_ntranslations"]
                package_metadata[lang_code]["ka_nphrases"]           = ka_metadata["phrases"] - package_metadata[lang_code]["kalite_nphrases"]

            # Now that we have metadata, compress by removing non-translated "translations"

    # Compile
    (out, err, rc) = compile_po_files(lang_codes=lang_codes)  # converts to django
    broken_langs = handle_po_compile_errors(lang_codes=lang_codes, out=out, err=err, rc=rc)

    return (package_metadata, broken_langs)


def upgrade_old_schema():
    """Move srt files from static/srt to locale directory and file them by language code, delete any old locale directories"""

    scrub_locale_paths()
    move_old_subtitles()

def handle_po_compile_errors(lang_codes=None, out=None, err=None, rc=None):
    """
    Return list of languages to not rezip due to errors in compile process.
    Then email admins errors.
    """

    broken_codes = re.findall(r'(?<=ka-lite/locale/)\w+(?=/LC_MESSAGES)', err) or []

    if lang_codes:
        # Only show the errors relevant to the list of language codes passed in.
        lang_codes = set([lcode_to_django_dir(lc) for lc in lang_codes])
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
                                 combine_with_po_file=None,
                                 rebuild=True,
                                 download_type=None):
    """
    Download latest translations from CrowdIn to corresponding locale
    directory. If zip_file is given, use that as the zip file
    instead of going through CrowdIn.

    """
    lang_code = lcode_to_ietf(lang_code)

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

        request_url = "http://api.crowdin.net/api/project/%s/download/%s.zip?key=%s" % (project_id, lang_code, project_key)
        try:
            resp = requests.get(request_url)
            resp.raise_for_status()
        except Exception as e:
            if resp.status_code == 404:
                logging.info("No translations found for language %s" % lang_code)
                return None  # no translations
            elif resp.status_code == 401:
                raise CommandError("401 Unauthorized while trying to access the CrowdIn API. Be sure to set CROWDIN_PROJECT_ID and CROWDIN_PROJECT_KEY in local_settings.py.")
            else:
                raise CommandError("%s - couldn't connect to CrowdIn API - cannot continue without downloading %s!" % (e, request_url))
        else:
            logging.info("Successfully downloaded zip archive")

        # Unpack into temp dir
        try:
            z = zipfile.ZipFile(StringIO.StringIO(resp.content))
        except Exception as e:
            logging.error("Error downloading zip file: % s" % e)
            z = None

        try:
            if zip_file:
                with open(zip_file, "wb") as fp:  # save the zip file
                    fp.write(resp.content)
        except Exception as e:
            logging.error("Error writing zip file to %s: %s" % (zip_file, e))

    tmp_dir_path = tempfile.mkdtemp()
    if z:
        z.extractall(tmp_dir_path)

    # Copy over new translations
    po_file = extract_new_po(tmp_dir_path, combine_with_po_file=combine_with_po_file, lang=lang_code, filter_type=download_type)

    # Clean up tracks
    if os.path.exists(tmp_dir_path):
        shutil.rmtree(tmp_dir_path)

    return po_file


def build_translations(project_id=settings.CROWDIN_PROJECT_ID, project_key=settings.CROWDIN_PROJECT_KEY):
    """Build latest translations into zip archive on CrowdIn."""

    logging.info("Requesting that CrowdIn build a fresh zip of our translations")
    request_url = "http://api.crowdin.net/api/project/%s/export?key=%s" % (project_id, project_key)
    try:
        resp = requests.get(request_url)
        resp.raise_for_status()
    except Exception as e:
        logging.error(e)


def extract_new_po(extract_path, combine_with_po_file=None, lang="all", filter_type=None):
    """Move newly downloaded po files to correct location in locale
    direction. Returns the location of the po file if a single
    language is given, or a list of locations if language is
    'all'.

    """

    if combine_with_po_file:
        assert lang != 'all', "You can only combine a po file with only one other po file. Please select a specific language, not 'all'."
        assert os.path.basename(combine_with_po_file) in ["django.po", "djangojs.po"], "File %s does not seem to be either django.po or djangojs.po."

    if lang == 'all':
        languages = os.listdir(extract_path)
        return [extract_new_po(os.path.join(extract_path, l), lang=l) for l in languages]

    converted_code = lcode_to_django_dir(lang)

    def prep_inputs(extract_path, converted_code, filter_type):
        src_po_files = all_po_files(extract_path)

        # remove all exercise po that is not about math
        if filter_type:
            if filter_type == "ka":
                for po_file in src_po_files:
                    name, _ext = os.path.splitext(po_file)

                # Magic # 4 below: 3 for .po, 1 for -  (-fr.po)
                src_po_files_learn     = filter(lambda fn: any([os.path.basename(fn).startswith(str) for str in ["learn."]]), src_po_files)
                src_po_files_videos    = filter(lambda fn: ".videos" in fn, src_po_files_learn)
                src_po_files_exercises = filter(lambda fn: ".exercises" in fn, src_po_files_learn)
                src_po_files_topics    = filter(lambda fn:  sum([po.startswith(fn[:-len(lang)-4]) for po in src_po_files_learn]) > 1, src_po_files_learn)
                src_po_files_topics   += filter(lambda fn: any([os.path.basename(fn).startswith(str) for str in ["content.chrome", "_other_"]]), src_po_files)

                src_po_files = src_po_files_videos + src_po_files_exercises + src_po_files_topics

                # before we call msgcat, process each exercise po file and leave out only the metadata
                for exercise_po in src_po_files_exercises:
                    remove_nonmetadata(exercise_po, r'.*(of|for) exercise')
                for video_po in src_po_files_videos:
                    remove_nonmetadata(video_po, r'.*(of|for) video')
                for topic_po in src_po_files_topics:
                    remove_nonmetadata(topic_po, r'.*(of|for) topic')

        if combine_with_po_file:
            yield combine_with_po_file

    src_po_files = prep_inputs(extract_path, converted_code, filter_type)


    @profile
    def produce_outputs(src_po_files, converted_code):
        if any(["admin-pl.po" in pofile for pofile in src_po_files]):
            import pdb; pdb.set_trace()
        # ensure directory exists in locale folder, and then overwrite local po files with new ones
        dest_path = os.path.join(LOCALE_ROOT, converted_code, "LC_MESSAGES")
        ensure_dir(dest_path)
        dest_file = os.path.join(dest_path, 'django.po')

        build_file = os.path.join(dest_path, 'djangobuild.po')  # so we dont clobber previous django.po that we build

        logging.info('Concatenating all po files found...')
        try:
            build_po = polib.pofile(build_file)
        except IOError as e:  # build_file doesn't exist yet
            build_po = polib.POFile(fpath=build_file)

        for src_file in src_po_files:
            src_file = zlib.decompress(src_file)  # ARON: this whole zlib.{de,}compress hack saves a megabyte. It counts!
            logging.debug('Concatenating %s with %s...' % (src_file, build_file))
            src_po = polib.pofile(src_file)
            build_po.merge(src_po)

        # de-obsolete messages
        for poentry in build_po:
            # ok build_po appears to be a list, but not actually one. Hence just doing
            # a list comprehension over it won't work. So we unobsolete entries so that
            # they can be detected and turned into a mo file
            poentry.obsolete = False
        build_po.save()
        shutil.move(build_file, dest_file)

        return dest_file

    dest_file = produce_outputs(src_po_files, converted_code)

    return dest_file


def get_po_metadata(pofilename):
    if not pofilename or not os.path.exists(pofilename):
        nphrases = 0
        ntranslations = 0
    else:
        pofile = polib.pofile(pofilename)
        nphrases = len(pofile)
        ntranslations = sum([int(po.msgid != po.msgstr) for po in pofile])

    return { "approved_translations": ntranslations, "phrases": nphrases }


def remove_nonmetadata(pofilename, METADATA_MARKER):
    '''Checks each message block in the po file given by pofilename, and
    sees if the top comment of each one has the string '(of|for)
    exercise'. If not, then it will be deleted from the po file.
    '''
    assert os.path.exists(pofilename), "%s does not exist!" % pofilename

    logging.info('Removing nonmetadata msgblocks from %s' % pofilename)
    pofile = polib.pofile(pofilename)

    clean_pofile = polib.POFile(encoding='utf-8')
    clean_pofile.append(pofile.metadata_as_entry())
    for msgblock in pofile:
        if re.match(EXERCISE_METADATA_LINE, msgblock.tcomment):
            # is exercise metadata, preserve
            clean_pofile.append(msgblock)

    os.remove(pofilename)
    clean_pofile.save(fpath=pofilename)

def get_exercise_po_files(po_files):
    return fnmatch.filter(po_files, '*.exercises-*.po')


def all_po_files(dir):
    '''Walks the directory dir and returns an iterable containing all the
    po files in the given directory.

    '''
    # return glob.glob(os.path.join(dir, '*/*.po'))
    for current_dir, _, filenames in os.walk(dir):
        for po_file in fnmatch.filter(filenames, '*.po'):
            if os.path.basename(po_file)[0] != '.':
                yield os.path.join(current_dir, po_file)


def generate_metadata(lang_codes=None, broken_langs=None, package_metadata=None):
    """Loop through locale folder, create or update language specific meta
    and create or update master file, skipping broken languages

    note: broken_langs must be in django format.

    """
    logging.info("Generating new language pack metadata")

    lang_codes = lang_codes or os.listdir(LOCALE_ROOT)
    master_metadata = softload_json(get_language_pack_availability_filepath(), logger=logging.warn, errmsg="Error opening master language pack metadata")

    # loop through all languages in locale, update master file
    crowdin_meta_dict = download_crowdin_metadata()

    for lc in lang_codes:
        lang_code_django = lcode_to_django_dir(lc)
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
        local_meta = softload_json(metadata_filepath, logger=logging.warn, errmsg="Error opening %s language pack metadata" % lc)

        try:
            updated_meta = package_metadata.get(lang_code_ietf, {})
            updated_meta.update({
                "code": lang_code_ietf,  # user-facing code
                "name": lang_name,
                "software_version": version.VERSION,
            })

        except LanguageNotFoundError:
            logging.error("Unrecognized language; must skip item %s" % lang_code_django)
            continue

        language_pack_version = increment_language_pack_version(local_meta, updated_meta)
        updated_meta["language_pack_version"] = language_pack_version
        local_meta.update(updated_meta)

        logging.debug("%s" % local_meta)

        # Write locally (this is used on download by distributed server to update it's database)
        with open(metadata_filepath, 'w') as output:
            json.dump(local_meta, output)

        # Update master (this is used for central server to handle API requests for data)
        master_metadata[lang_code_ietf] = local_meta

    # Save updated master
    ensure_dir(os.path.dirname(get_language_pack_availability_filepath()))
    with open(get_language_pack_availability_filepath(), 'w') as output:
        json.dump(master_metadata, output)
    logging.info("Local record of translations updated")


def update_metadata(updated_metadata):
    """
    We've zipped the packages, and now have unzipped & zipped sizes.
    Update this info in the local metadata (but not inside the zip)
    """
    master_metadata = softload_json(get_language_pack_availability_filepath(), logger=logging.warn, errmsg="Error opening master language pack metadata")

    for lc, meta in updated_metadata.iteritems():
        lang_code_ietf = lcode_to_ietf(lc)

        # Gather existing metadata
        metadata_filepath = get_language_pack_metadata_filepath(lang_code_ietf)
        local_meta = softload_json(metadata_filepath, logger=logging.warn, errmsg="Error opening %s language pack metadata" % lc)

        for att, val in meta.iteritems():
            local_meta[att] = val

        # Write locally (this is used on download by distributed server to update it's database)
        with open(metadata_filepath, 'w') as output:
            json.dump(local_meta, output)

        # Update master (this is used for central server to handle API requests for data)
        master_metadata[lang_code_ietf] = local_meta

    # Save updated master
    ensure_dir(os.path.dirname(get_language_pack_availability_filepath()))
    with open(get_language_pack_availability_filepath(), 'w') as output:
        json.dump(master_metadata, output)
    logging.info("Local record of translations updated")


def download_crowdin_metadata(project_id=settings.CROWDIN_PROJECT_ID, project_key=settings.CROWDIN_PROJECT_KEY):
    """Return tuple in format (total_strings, total_translated, percent_translated)"""

    request_url = "http://api.crowdin.net/api/project/%s/status?key=%s&json=True" % (project_id, project_key)
    try:
        resp = requests.get(request_url)
        resp.raise_for_status()
        crowdin_meta_dict = json.loads(resp.content)
    except Exception as e:
        logging.error("Error getting crowdin metadata: %s" % e)
        crowdin_meta_dict = {}
    return crowdin_meta_dict


def increment_language_pack_version(local_meta, updated_meta):
    """Increment language pack version if translations have been updated
(start over if software version has incremented)
    """
    for att in VERSION_CHANGING_ATTRIBUTES:
        assert att in updated_meta, "All VERSION_CHANGING_ATTRIBUTES must be set (%s is not?)" % att

    if not local_meta or version_diff(local_meta.get("software_version"), version.VERSION) < 0:
        # set to one for the first time, or if this is the first build of a new software version
        logging.info("Setting %s language pack version to 1" % updated_meta["code"])
        language_pack_version = 1

    else:
        # Search for any attributes that would cause a version change.
        language_pack_version = local_meta.get("language_pack_version", 1)

        for att in VERSION_CHANGING_ATTRIBUTES:
            if local_meta.get(att) != updated_meta.get(att):
                language_pack_version += 1
                logging.debug("Increasing %s language pack version to %d" % (local_meta["code"], language_pack_version))
                break

    return language_pack_version


def zip_language_packs(lang_codes=None):
    """Zip up and expose all language packs

    converts all into ietf
    """
    sizes = {}
    lang_codes = lang_codes or os.listdir(LOCALE_ROOT)
    lang_codes = [lcode_to_ietf(lc) for lc in lang_codes]
    logging.info("Zipping up %d language pack(s)" % len(lang_codes))

    for lang_code_ietf in lang_codes:
        lang_code_django = lcode_to_django_dir(lang_code_ietf)
        lang_locale_path = os.path.join(LOCALE_ROOT, lang_code_django)
        sizes[lang_code_ietf] = { "package_size": 0, "zip_size": 0}

        if not os.path.exists(lang_locale_path):
            logging.warn("Unexpectedly skipping missing directory: %s" % lang_code_django)
        elif not os.path.isdir(lang_locale_path):
            logging.error("Skipping language where a file exists where a directory was expected: %s" % lang_code_django)

        # Create a zipfile for this language
        zip_filepath = get_language_pack_filepath(lang_code_ietf)
        ensure_dir(os.path.dirname(zip_filepath))
        logging.info("Creating zip file in %s" % zip_filepath)
        z = zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED)

        for metadata_file in glob.glob('%s/*.json' % lang_locale_path):
            # Get every single file in the directory and zip it up
            filepath = os.path.join(lang_locale_path, metadata_file)
            z.write(filepath, arcname=os.path.basename(metadata_file))
            sizes[lang_code_ietf]["package_size"] += os.path.getsize(filepath)

        for mo_file in glob.glob('%s/LC_MESSAGES/*.mo' % lang_locale_path):
            # Get every single compiled language file
            filepath = os.path.join(lang_locale_path, mo_file)
            z.write(filepath, arcname=os.path.join("LC_MESSAGES", os.path.basename(mo_file)))
            sizes[lang_code_ietf]["package_size"] += os.path.getsize(filepath)

        for srt_file in glob.glob('%s/subtitles/*.srt' % lang_locale_path):
            # Get every single subtitle
            filepath = os.path.join(lang_locale_path, srt_file)
            z.write(filepath, arcname=os.path.join("subtitles", os.path.basename(srt_file)))
            sizes[lang_code_ietf]["package_size"] += os.path.getsize(filepath)

        exercises_dirpath = get_localized_exercise_dirpath(lang_code_ietf)
        for exercise_file in glob.glob(os.path.join(exercises_dirpath, "*.html")):
            # Get every single compiled language file
            filepath = os.path.join(exercises_dirpath, exercise_file)
            z.write(filepath, arcname=os.path.join("exercises", os.path.basename(exercise_file)))
            sizes[lang_code_ietf]["package_size"] += os.path.getsize(filepath)

        # Add dubbed video map
        z.write(DUBBED_VIDEOS_MAPPING_FILEPATH, arcname=os.path.join("dubbed_videos", os.path.basename(DUBBED_VIDEOS_MAPPING_FILEPATH)))
        sizes[lang_code_ietf]["package_size"] += os.path.getsize(DUBBED_VIDEOS_MAPPING_FILEPATH)

        z.close()
        sizes[lang_code_ietf]["zip_size"]= os.path.getsize(zip_filepath)

    logging.info("Done.")
    return sizes
