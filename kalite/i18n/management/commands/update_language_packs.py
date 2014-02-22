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
import copy
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
from collections import Iterable, defaultdict
from itertools import chain, ifilter
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.core.mail import mail_admins

import settings
from .update_po import compile_po_files
from i18n import *
from settings import LOG as logging
from updates import get_all_remote_video_sizes
from utils.general import datediff, ensure_dir, softload_json, version_diff
from version import VERSION


# Attributes whose value, if changed, should change the version of the language pack.
VERSION_CHANGING_ATTRIBUTES = ["approved_translations", "phrases", "subtitle_count", "num_dubbed_videos", "num_exercises"]

class SkipTranslations(Exception):
    pass

class Command(BaseCommand):
    help = 'Updates all requested language packs'

    option_list = BaseCommand.option_list + (
        make_option('-d', '--days',
                    action='store',
                    dest='days',
                    default=1 if not settings.DEBUG else 365,
                    metavar="NUM_DAYS",
                    help="Update any and all subtitles that haven't been refreshed in the numebr of days given. Defaults to 0 days."),
        make_option('-l', '--lang_codes',
                    action='store',
                    dest='lang_codes',
                    default=None,
                    metavar="LANG_CODES",
                    help="Language codes to update (comma-delimited list) (default: all known)"),
        make_option('--no-srts',
                    action='store_false',
                    dest='update_srts',
                    default=True,
                    help='Do not refresh video subtitles before bundling.'),
        make_option('--no-kalite-trans',
                    action='store_false',
                    dest='update_kalite_trans',
                    default=True,
                    help='Do not refresh KA Lite content translations before bundling.'),
        make_option('--no-ka-trans',
                    action='store_false',
                    dest='update_ka_trans',
                    default=True,
                    help='Do not refresh Khan Academy content translations before bundling.'),
        make_option('--no-exercises',
                    action='store_false',
                    dest='update_exercises',
                    default=True,
                    help='Do not refresh Khan Academy exercises before bundling.'),
        make_option('--no-dubbed',
                    action='store_false',
                    dest='update_dubbed',
                    default=True,
                    help='Do not refresh Khan Academy dubbed video mappings.'),
        make_option('--no-update',
                    action='store_true',
                    dest='no_update',
                    default=False,
                    help='Do not refresh any resources before packaging.'),
        make_option('--low-mem',
                    action='store_true',
                    dest='low_mem',
                    default=True,
                    help='Limit the memory used by the command by making the garbage collector more aggressive.'),
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
        make_option('--force-update',
                    action='store_true',
                    dest='force_update',
                    default=False,
                    help='Force the language pack version to update.'),
        make_option('-o', '--use_local',
                    action='store_true',
                    dest='use_local',
                    default=False,
                    metavar="USE_LOCAL",
                    help="Use the local po files, instead of refreshing from online (a way to test translation tweaks)"),
        make_option('-e', '--ver',
                    action='store',
                    dest='version',
                    default=VERSION,
                    metavar="VERSION",
                    help="Output version"),
    )

    def handle(self, *args, **options):

        # Check that we can run
        if not settings.CENTRAL_SERVER:
            raise CommandError("This must only be run on the central server.")
        supported_langs = get_supported_languages()
        if not options["lang_codes"]:
            lang_codes = supported_langs
        else:
            requested_codes = set(options["lang_codes"].split(","))
            lang_codes = [lcode_to_ietf(lc) for lc in requested_codes if lc in supported_langs]
            unsupported_codes = requested_codes - set(lang_codes)
            if unsupported_codes:
                raise CommandError("Requested unsupported languages: %s" % sorted(list(unsupported_codes)))

        # Scrub options
        for key in options:
            # If no_update is set, then disable all update options.
            if key.startswith("update_"):
                options[key] = options[key] and not options["no_update"]

        if version_diff(options["version"], "0.10.3") < 0:
            raise CommandError("This command cannot be used for versions before 0.10.3")

        if options['low_mem']:
            logging.info('Making the GC more aggressive...')
            gc.set_threshold(36, 2, 2)

        # For dealing with central server changes across versions
        upgrade_old_schema()

        # Now, we're going to build the language packs, collecting metadata long the way.
        package_metadata = update_language_packs(lang_codes, options)


def update_language_packs(lang_codes, options):

    package_metadata = {}

    since_date = datetime.datetime.now() - datetime.timedelta(int(options["days"]))

    if options['update_dubbed']:
        # Get the latest dubbed video map; it's shared across language packs
        force_dubbed_download = not os.path.exists(DUBBED_VIDEOS_MAPPING_FILEPATH) \
            or 0 < datediff(since_date, datetime.datetime.fromtimestamp(os.path.getctime(DUBBED_VIDEOS_MAPPING_FILEPATH)))
        get_dubbed_video_map(force=force_dubbed_download)

    for lang_code in lang_codes:
        lang_code_map = get_supported_language_map(lang_code)
        lang_metadata = {}

        # Step 1: Update / collect srts.  No version needed, we want to share latest always.
        if options['update_srts']:
            update_srts(since_date=since_date, lang_codes=[lang_code_map["amara"]])
        lang_metadata["subtitle_count"] = get_subtitle_count(lang_code_map["amara"])

        # Step 2: Update the dubbed video mappings. No version needed, we want to share latest always.
        dv_map = get_dubbed_video_map(lang_code_map["dubbed_videos"])
        lang_metadata["num_dubbed_videos"] = len(dv_map) if dv_map and version_diff(options["version"], "0.10.3") > 0 else 0

        # Step 3: Update the exercises.  No version needed, we want to share latest always.
        #  TODO(bcipolli): make sure that each language pack only grabs exercises that are included in its topic tree.
        if options['update_exercises'] and version_diff(options["version"], "0.10.3") > 0:
            call_command("scrape_exercises", lang_code=lang_code_map["exercises"])
        lang_metadata["num_exercises"] = get_localized_exercise_count(lang_code_map["exercises"]) if version_diff(options["version"], "0.10.3") > 0 else 0

        # Step 4: Update the crowdin translations.  Version needed!
        #   TODO(bcipolli): skip this when we're going backwards in version.
        if options["no_update"] or version_diff(options["version"], "0.10.3") == 0:
            trans_metadata = {lang_code: get_po_metadata(get_po_build_path(lang_code))}
        else:
            try:
                trans_metadata = update_translations(
                    lang_codes=[lang_code],  # will be converted, as needed
                    zip_file=options['zip_file'],
                    ka_zip_file=options['ka_zip_file'],
                    download_ka_translations=options['update_ka_trans'],
                    download_kalite_translations=options['update_kalite_trans'],
                    use_local=options["use_local"],
                    version=options["version"],
                )
            except SkipTranslations:
                trans_metadata = {lang_code: get_po_metadata(get_po_build_path(lang_code))}
        lang_metadata.update(trans_metadata.get(lang_code, {}))

        # Now create/update unified meta data

        generate_metadata(package_metadata={lang_code: lang_metadata}, version=options["version"], force_version_update=options["force_update"])

        # Zip into language packs
        package_sizes = zip_language_packs(lang_codes=[lang_code], version=options["version"])
        logging.debug("%s sizes: %s" % (lang_code, package_sizes.get(lang_code, {})))

        lang_metadata.update(package_sizes.get(lang_code, {}))

        # Update the metadata with the package size information
        update_metadata({lang_code: lang_metadata}, version=options["version"])

        # Update package metadata
        package_metadata[lang_code] = lang_metadata

    return package_metadata


def update_srts(since_date, lang_codes):
    """
    Run the commands to update subtitles that haven't been updated in the number of days provided.
    Default is to update all srt files that haven't been requested in 30 days
    """
    date_as_str = '{0.month}/{0.day}/{0.year}'.format(since_date)
    logging.info("Updating subtitles that haven't been refreshed since %s" % date_as_str)
    call_command("generate_subtitle_map", date_since_attempt=date_as_str)
    if lang_codes:
        for lang_code in lang_codes:
            call_command("cache_subtitles", date_since_attempt=date_as_str, lang_code=lang_code)
    else:
        call_command("cache_subtitles", date_since_attempt=date_as_str)


def get_po_build_path(lang_code, po_file="django.po", dest_path=None, version=VERSION):
    dest_path = dest_path or get_lp_build_dir(lang_code, version=version)
    return  os.path.join(dest_path, po_file)

def update_translations(lang_codes=None,
                        download_kalite_translations=True,
                        download_ka_translations=True,
                        zip_file=None,
                        ka_zip_file=None,
                        use_local=False,
                        version=VERSION):
    """
    Download translations (if necessary), repurpose them into needed files,
    then move the resulting files to the versioned storage directory.
    """
    package_metadata = {}

    if use_local:
        for lang_code in lang_codes:
            lang_code = lcode_to_ietf(lang_code)
            package_metadata[lang_code] = {}
            combined_po_file = get_po_build_path(lang_code, version=version)
            combined_metadata = get_po_metadata(combined_po_file)
            package_metadata[lang_code]["approved_translations"] = combined_metadata["approved_translations"]
            package_metadata[lang_code]["phrases"]               = combined_metadata["phrases"]

    else:
        logging.info("Downloading %s language(s)" % lang_codes)

        # Download latest UI translations from CrowdIn


        for lang_code in (lang_codes or [None]):
            lang_code = lcode_to_ietf(lang_code)
            lang_code_crowdin = get_supported_language_map(lang_code)['crowdin']
            if not lang_code_crowdin:
                logging.warning('Interface translations for %s are disabled for now' % lang_code)
                raise SkipTranslations

            # we make it a defaultdict so that if no value is present it's automatically 0
            package_metadata[lang_code] = defaultdict(
                lambda: 0,
                {
                    'approved_translations': 0,
                    'phrases': 0,
                    'kalite_ntranslations': 0,
                    'kalite_nphrases': 0,
                })                   # these values will likely yield the wrong values when download_kalite_translations == False.

            if not download_kalite_translations:
                logging.info("Skipping KA Lite translations")
                kalite_po_file = None
            else:
                logging.info("Downloading KA Lite translations...")
                kalite_po_file = download_latest_translations(
                    lang_code=lang_code_crowdin,
                    project_id=settings.CROWDIN_PROJECT_ID,
                    project_key=settings.CROWDIN_PROJECT_KEY,
                    zip_file=zip_file or (os.path.join(CROWDIN_CACHE_DIR, "kalite-%s.zip" % lang_code_crowdin) if settings.DEBUG else None),
                )

            # We have the po file, now get metadata.
            kalite_metadata = get_po_metadata(kalite_po_file)
            package_metadata[lang_code]["approved_translations"] = kalite_metadata["approved_translations"]
            package_metadata[lang_code]["phrases"]               = kalite_metadata["phrases"]
            package_metadata[lang_code]["kalite_ntranslations"]  = kalite_metadata["approved_translations"]
            package_metadata[lang_code]["kalite_nphrases"]       = kalite_metadata["phrases"]

            # Download Khan Academy translations too
            if not download_ka_translations:
                logging.info("Skipping KA translations")
                combined_po_file = None
            else:
                logging.info("Downloading Khan Academy translations...")
                combined_po_file = download_latest_translations(
                    lang_code=lang_code_crowdin,
                    project_id=settings.KA_CROWDIN_PROJECT_ID,
                    project_key=settings.KA_CROWDIN_PROJECT_KEY,
                    zip_file=ka_zip_file or (os.path.join(CROWDIN_CACHE_DIR, "ka-%s.zip" % lang_code_crowdin) if settings.DEBUG else None),
                    combine_with_po_file=kalite_po_file,
                    rebuild=False,  # just to be friendly to KA--we shouldn't force a rebuild
                    download_type="ka",
                )

            # we have the po file; now
            ka_metadata = get_po_metadata(combined_po_file)
            package_metadata[lang_code]["approved_translations"] = ka_metadata["approved_translations"]
            package_metadata[lang_code]["phrases"]               = ka_metadata["phrases"]
            package_metadata[lang_code]["ka_ntranslations"]      = ka_metadata["approved_translations"] - package_metadata[lang_code]["kalite_ntranslations"]
            package_metadata[lang_code]["ka_nphrases"]           = ka_metadata["phrases"] - package_metadata[lang_code]["kalite_nphrases"]


            # here we compute the percent translated
            if download_ka_translations or download_kalite_translations:
                pmlc = package_metadata[lang_code] # shorter name, less characters
                if pmlc['kalite_nphrases'] == pmlc['ka_nphrases'] == 0:
                    pmlc['percent_translated'] = 0
                else:
                    pmlc["percent_translated"] = 100. * (pmlc['kalite_ntranslations'] + pmlc['ka_ntranslations']) / float(pmlc['kalite_nphrases'] + pmlc['ka_nphrases'])


            # english is always 100% translated
            if lang_code == 'en':
                pmlc['percent_translated'] = 100

    return package_metadata


def upgrade_old_schema():
    """Move srt files from static/srt to locale directory and file them by language code, delete any old locale directories"""

    scrub_locale_paths()

    #refactor_central_locale_folders(src_dir=LOCALE_ROOT, dest_dir=LANGUAGE_PACK_BUILD_DIR)

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

def download_latest_translations(project_id=None,
                                 project_key=None,
                                 lang_code="all",
                                 zip_file=None,
                                 combine_with_po_file=None,
                                 rebuild=True,
                                 download_type=None):
    """
    Download latest translations from CrowdIn to corresponding locale
    directory. If zip_file is given, use that as the zip file
    instead of going through CrowdIn.

    Arguments:
    - project_id -- the project ID in CrowdIn
    - project_key -- the secret key used for accessing the po files in CrowdIn
    - zip_file -- the location of a cached zip file. Stores the downloaded zip file in this location if nonexistent.
    - rebuild -- ask CrowdIn to rebuild translations. Default is False.
    - download_type -- whether it is a ka or ka_lite. Default is None, meaning ka_lite.

    """
    if not project_id:
        project_id = settings.CROWDIN_PROJECT_ID
    if not project_key:
       project_key = settings.CROWDIN_PROJECT_KEY

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
    po_file = build_new_po(
        lang_code=lang_code,
        src_path=tmp_dir_path,
        dest_path=get_lp_build_dir(lang_code, version=VERSION),  # put latest translations into newest version.
        combine_with_po_file=combine_with_po_file,
        filter_type=download_type,
    )

    # Clean up tracks
    if os.path.exists(tmp_dir_path):
        shutil.rmtree(tmp_dir_path)

    return po_file


def build_translations(project_id=None, project_key=None):
    """Build latest translations into zip archive on CrowdIn."""

    if not project_id:
        project_id = settings.CROWDIN_PROJECT_ID
    if not project_key:
       project_key = settings.CROWDIN_PROJECT_KEY

    logging.info("Requesting that CrowdIn build a fresh zip of our translations")
    request_url = "http://api.crowdin.net/api/project/%s/export?key=%s" % (project_id, project_key)
    try:
        resp = requests.get(request_url)
        resp.raise_for_status()
    except Exception as e:
        logging.error(e)


def build_new_po(lang_code, src_path, dest_path=None, combine_with_po_file=None, filter_type=None, version=VERSION):
    """Move newly downloaded po files to correct location in locale
    direction. Returns the location of the po file if a single
    language is given, or a list of locations if language is
    'all'.

    """
    lang_code = lcode_to_django_dir(lang_code)
    dest_path = dest_path or get_lp_build_dir(lang_code, version=version)

    def prep_inputs(src_path, lang_code, filter_type):
        src_po_files = [po for po in all_po_files(src_path)]

        # remove all exercise po that is not about math
        if filter_type == "ka":

            # Magic # 4 below: 3 for .po, 1 for -  (-fr.po)
            src_po_files_learn     = ifilter(lambda fn: any([os.path.basename(fn).startswith(str) for str in ["learn."]]), src_po_files)
            src_po_files_learn     = [po for po in src_po_files_learn]

            src_po_files_videos    = ifilter(lambda fn: ".videos" in fn, src_po_files_learn)
            src_po_files_exercises = ifilter(lambda fn: ".exercises" in fn, src_po_files_learn)
            src_po_files_topics    = ifilter(lambda fn:  sum([po.startswith(fn[:-len(lang_code)-4]) for po in src_po_files_learn]) > 1, src_po_files_learn)
            src_po_files_topics    = chain(
                src_po_files_topics,
                ifilter(lambda fn: any([os.path.basename(fn).startswith(str) for str in ["content.chrome", "_other_"]]), src_po_files)
            )

            # before we call msgcat, process each exercise po file and leave out only the metadata
            filter_rules = ((r'.*(of|for) exercise', src_po_files_exercises),
                            (r'.*(of|for) video', src_po_files_videos),
                            (r'.*(of|for) topic', src_po_files_topics))
            for rule, src_file_list in filter_rules:
                for po_file in src_file_list:
                    try:
                        remove_nonmetadata(po_file, rule)
                        yield po_file
                    except IOError: # either a parse error from polib, or file doesnt exist
                        # TODO (ARON): capture all po files that return this error, show it to user
                        continue

        else:
            for po_file in src_po_files:
                yield po_file

        if combine_with_po_file:
            yield combine_with_po_file
    src_po_files = prep_inputs(src_path, lang_code, filter_type)


    def produce_outputs(src_po_files, dest_path, lang_code):
        # ensure directory exists in locale folder, and then overwrite local po files with new ones
        ensure_dir(dest_path)

        dest_file = os.path.join(dest_path, 'django.po')
        dest_mo_file = os.path.join(dest_path, 'django.mo')

        build_file = os.path.join(dest_path, 'djangobuild.po')  # so we dont clobber previous django.po that we build

        logging.info('Concatenating all po files found...')
        try:
            build_po = polib.pofile(build_file)
        except IOError as e:  # build_file doesn't exist yet
            build_po = polib.POFile(fpath=build_file)

        for src_file in src_po_files:
            if os.path.basename(src_file).startswith('kalitejs'):
                logging.debug('Compiling %s on its own...' % src_file)
                js_po_file = polib.pofile(src_file)
                js_mo_file = os.path.join(dest_path, 'djangojs.mo')
                js_po_file.save(os.path.join(dest_path, 'djangojs.po'))
                js_po_file.save_as_mofile(js_mo_file)
            else:
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
        build_po.save_as_mofile(dest_mo_file)
        shutil.move(build_file, dest_file)

        return dest_file

    dest_file = produce_outputs(src_po_files, dest_path, lang_code)

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
        if re.match(METADATA_MARKER, msgblock.tcomment):
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


def generate_metadata(package_metadata=None, version=VERSION, force_version_update=False):
    """Loop through locale folder, create or update language specific meta
    and create or update master file, skipping broken languages
    """
    logging.info("Generating new language pack metadata")

    lang_codes = package_metadata.keys() if package_metadata else os.listdir(LOCALE_ROOT)
    broken_langs = [lc for lc, md in package_metadata.iteritems() if md.get("broken")] if package_metadata else []

    master_filepath = get_language_pack_availability_filepath(version=version)
    master_metadata = softload_json(master_filepath, logger=logging.warn, errmsg="Error opening master language pack metadata")

    # loop through all languages in locale, update master file
    crowdin_meta_dict = download_crowdin_metadata()

    for lc in lang_codes:
        lang_code_django = lcode_to_django_dir(lc)
        lang_code_ietf = lcode_to_ietf(lc)
        lang_name = get_language_name(lang_code_ietf)
        metadata_filepath = get_language_pack_metadata_filepath(lang_code_ietf, version=version)
        ensure_dir(os.path.dirname(metadata_filepath))

        if broken_langs and lang_code_django in broken_langs:  # broken_langs is django format
            logging.info("Skipping directory %s because it did not compile." % lang_code_django)
            continue

        # Gather existing metadata
        crowdin_meta = next((meta for meta in crowdin_meta_dict if meta["code"] == lang_code_ietf), {})
        stored_meta = softload_json(metadata_filepath, logger=logging.info, errmsg="Could not open %s language pack metadata" % lc)

        updated_meta = package_metadata.get(lang_code_ietf) or {}
        updated_meta.update({
            "code": lang_code_ietf,  # user-facing code
            "name": lang_name,
            "software_version": version,
        })

        try:
            # Augment the metadata
            updated_meta.update(get_language_names(lang_code_django))
        except LanguageNotFoundError:
            logging.warning("Unrecognized language; unable to add extra naming metadata %s" % lang_code_django)
            continue

        if force_version_update:
            language_pack_version = 1 + stored_meta.get("language_pack_version", 0)  # will increment to one
        else:
            language_pack_version = increment_language_pack_version(stored_meta, updated_meta)

        updated_meta["language_pack_version"] = language_pack_version
        stored_meta.update(updated_meta)

        # Write locally (this is used on download by distributed server to update it's database)
        with open(metadata_filepath, 'w') as output:
            json.dump(stored_meta, output)

        # Update master (this is used for central server to handle API requests for data)
        master_metadata[lang_code_ietf] = stored_meta

    # Save updated master
    ensure_dir(os.path.dirname(master_filepath))
    with open(master_filepath, 'w') as fp:
        json.dump(master_metadata, fp)
    logging.info("Local record of translations updated")


def update_metadata(package_metadata, version=VERSION):
    """
    We've zipped the packages, and now have unzipped & zipped sizes.
    Update this info in the local metadata (but not inside the zip)
    """
    master_filepath = get_language_pack_availability_filepath(version=version)
    master_metadata = softload_json(master_filepath, logger=logging.warn, errmsg="Error opening master language pack metadata")

    for lc, updated_meta in package_metadata.iteritems():
        lang_code_ietf = lcode_to_ietf(lc)

        # Gather existing metadata
        metadata_filepath = get_language_pack_metadata_filepath(lang_code_ietf, version=version)
        stored_meta = softload_json(metadata_filepath, logger=logging.warn, errmsg="Error opening %s language pack metadata" % lc)

        stored_meta.update(updated_meta)

        # Write locally (this is used on download by distributed server to update it's database)
        with open(metadata_filepath, 'w') as output:
            json.dump(stored_meta, output)

        # Update master (this is used for central server to handle API requests for data)
        master_metadata[lang_code_ietf] = stored_meta

    # Save updated master
    ensure_dir(os.path.dirname(master_filepath))
    with open(master_filepath, 'w') as output:
        json.dump(master_metadata, output)
    logging.info("Local record of translations updated")


def download_crowdin_metadata(project_id=None, project_key=None):
    """Return tuple in format (total_strings, total_translated, percent_translated)"""

    if not project_id:
        project_id = settings.CROWDIN_PROJECT_ID
    if not project_key:
        project_key = settings.CROWDIN_PROJECT_KEY

    request_url = "http://api.crowdin.net/api/project/%s/status?key=%s&json=True" % (project_id, project_key)
    try:
        resp = requests.get(request_url)
        resp.raise_for_status()
        crowdin_meta_dict = json.loads(resp.content)
    except Exception as e:
        logging.error("Error getting crowdin metadata: %s" % e)
        crowdin_meta_dict = {}
    return crowdin_meta_dict

def increment_language_pack_version(stored_meta, updated_meta):
    """Increment language pack version if translations have been updated
(start over if software version has incremented)
    """

    for att in VERSION_CHANGING_ATTRIBUTES:
        # Everything is OK except for stored_metadata to contain something
        #   that updated_metadata does not.
        in_updated = att in updated_meta
        in_stored = att in stored_meta
        assert (not in_stored) or in_updated, "VERSION_CHANGING_ATTRIBUTES %s not contained in the update." % att
    assert "software_version" not in stored_meta or stored_meta["software_version"] == updated_meta["software_version"], "Metadata must be a version match."

    # Search for any attributes that would cause a version change.
    language_pack_version = stored_meta.get("language_pack_version", 0)  # will increment to one

    for att in VERSION_CHANGING_ATTRIBUTES:
        if stored_meta.get(att) != updated_meta.get(att):
            language_pack_version += 1
            logging.debug("Increasing %s language pack version to %d" % (updated_meta["code"], language_pack_version))
            break

    return language_pack_version


def zip_language_packs(lang_codes=None, version=VERSION):
    """Zip up and expose all language packs

    converts all into ietf
    """
    sizes = {}
    lang_codes = lang_codes or os.listdir(LANGUAGE_PACK_BUILD_DIR)
    lang_codes = [lcode_to_ietf(lc) for lc in lang_codes]
    logging.info("Zipping up %d language pack(s)" % len(lang_codes))

    for lang_code_ietf in lang_codes:
        lang_code_map = get_supported_language_map(lang_code_ietf)

        # Initialize values
        sizes[lang_code_ietf] = { "package_size": 0, "zip_size": 0}

        #
        lang_locale_path = get_lp_build_dir(lang_code_ietf, version=version)
        if not os.path.exists(lang_locale_path):
            logging.warn("Unexpectedly skipping missing directory: %s" % lang_code_ietf)
        elif not os.path.isdir(lang_locale_path):
            logging.error("Skipping language where a file exists where a directory was expected: %s" % lang_code_ietf)

        # Create a zipfile for this language
        zip_filepath = get_language_pack_filepath(lang_code_ietf, version=version)
        ensure_dir(os.path.dirname(zip_filepath))
        logging.info("Creating zip file in %s" % zip_filepath)
        z = zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED)

        # Get metadata from the versioned directory
        for metadata_file in glob.glob('%s/*.json' % get_lp_build_dir(lang_code_ietf, version=version)):
            # Get every single file in the directory and zip it up
            filepath = os.path.join(lang_locale_path, metadata_file)
            z.write(filepath, arcname=os.path.basename(metadata_file))
            sizes[lang_code_ietf]["package_size"] += os.path.getsize(filepath)

        # Get mo files from the directory
        lang_code_crowdin = lang_code_map["crowdin"]
        mo_files = glob.glob('%s/*.mo' % get_lp_build_dir(lcode_to_ietf(lang_code_crowdin), version=version)) if lang_code_crowdin else []
        for mo_file in mo_files:
            # Get every single compiled language file
            filepath = os.path.join(lang_locale_path, mo_file)
            z.write(filepath, arcname=os.path.join("LC_MESSAGES", os.path.basename(mo_file)))
            sizes[lang_code_ietf]["package_size"] += os.path.getsize(filepath)

        # include video file sizes
        remote_video_size_list = get_all_remote_video_sizes()
        z.writestr('video_file_sizes.json', str(remote_video_size_list))

        srt_dirpath = get_srt_path(lcode_to_django_dir(lang_code_map["amara"]))
        for srt_file in glob.glob(os.path.join(srt_dirpath, "*.srt")):
            z.write(srt_file, arcname=os.path.join("subtitles", os.path.basename(srt_file)))
            sizes[lang_code_ietf]["package_size"] += os.path.getsize(srt_file)

        if version_diff(version, "0.10.3") > 0:  # since these are globally available, need to check version.
            exercises_dirpath = get_localized_exercise_dirpath(lang_code_map["exercises"])
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
