"""
Downloads a language pack, unzips the contents, then moves files accordingly
"""
import glob
import os
import shutil
import zipfile
from optparse import make_option
from StringIO import StringIO

from django.conf import settings; logging = settings.LOG
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils.translation import ugettext as _

from .classes import UpdatesStaticCommand
from ... import REMOTE_VIDEO_SIZE_FILEPATH
from fle_utils.chronograph.management.croncommand import CronCommand
from fle_utils.general import ensure_dir
from fle_utils.internet.download import callback_percent_proxy, download_file
from kalite import caching
from kalite.i18n import get_localized_exercise_dirpath, get_srt_path, get_po_filepath, get_language_pack_url, get_language_name
from kalite.i18n import lcode_to_django_dir, lcode_to_ietf, update_jsi18n_file
from kalite.version import SHORTVERSION


class Command(UpdatesStaticCommand, CronCommand):
    help = "Download language pack requested from central server"

    unique_option_list = (
        make_option('-l', '--language',
                    action='store',
                    dest='lang_code',
                    default=settings.LANGUAGE_CODE,
                    metavar="LANG_CODE",
                    help="Specify a particular language code to download language pack for."),
        make_option('-s', '--software_version',
                    action='store',
                    dest='software_version',
                    default=SHORTVERSION,
                    metavar="SOFT_VERS",
                    help="Specify the software version to download a language pack for."),
        make_option('-f', '--from-file',
                    action='store',
                    dest='file',
                    default=None,
                    help='Use the given zip file instead of fetching from the central server.'),
    )

    option_list = UpdatesStaticCommand.option_list + CronCommand.unique_option_list + unique_option_list

    stages = (
        "download_language_pack",
        "unpack_language_pack",
        "add_js18n_file",
        "move_files",
        "collectstatic",
        "invalidate_caches",
    )

    def handle(self, *args, **options):
        if settings.CENTRAL_SERVER:
            raise CommandError("This must only be run on distributed servers server.")

        lang_code = lcode_to_ietf(options["lang_code"])
        lang_name = get_language_name(lang_code)
        software_version = options["software_version"]
        logging.info("Downloading language pack for lang_name=%s, software_version=%s" % (lang_name, software_version))

        # Download the language pack
        try:
            if options['file']:
                self.start(_("Using local language pack '%(filepath)s'") % {"filepath": options['file']})
                zip_filepath = options['file']
            else:
                self.start(_("Downloading language pack '%(lang_code)s'") % {"lang_code": lang_code})
                zip_filepath = get_language_pack(lang_code, software_version, callback=self.cb)

            # Unpack into locale directory
            self.next_stage(_("Unpacking language pack '%(lang_code)s'") % {"lang_code": lang_code})
            unpack_language(lang_code, zip_filepath=zip_filepath)

            #
            self.next_stage(_("Creating static files for language pack '%(lang_code)s'") % {"lang_code": lang_code})
            update_jsi18n_file(lang_code)


            self.next_stage(_("Moving files to their appropriate local disk locations."))
            move_dubbed_video_map(lang_code)
            move_exercises(lang_code)
            move_srts(lang_code)
            move_video_sizes_file(lang_code)

            self.next_stage()
            call_command("collectstatic", interactive=False)

            self.next_stage(_("Invalidate caches"))
            caching.invalidate_all_caches()

            self.complete((_("Finished processing language pack %(lang_name)s.") % {"lang_name": get_language_name(lang_code)}) +
                " Please restart the server to complete installation of the language pack.")
        except Exception as e:
            self.cancel(stage_status="error", notes=_("Error: %(error_msg)s") % {"error_msg": unicode(e)})
            raise

    def cb(self, percent):
        self.update_stage(stage_percent=percent/100.)

def get_language_pack(lang_code, software_version, callback):
    """Download language pack for specified language"""

    lang_code = lcode_to_ietf(lang_code)
    logging.info("Retrieving language pack: %s" % lang_code)
    request_url = get_language_pack_url(lang_code, software_version)
    logging.debug("Downloading zip from %s" % request_url)
    path, response = download_file(request_url, callback=callback_percent_proxy(callback))
    return path

def unpack_language(lang_code, zip_filepath=None, zip_fp=None, zip_data=None):
    """Unpack zipped language pack into locale directory"""
    lang_code = lcode_to_django_dir(lang_code)

    logging.info("Unpacking new translations")
    ensure_dir(get_po_filepath(lang_code=lang_code))

    ## Unpack into temp dir
    z = zipfile.ZipFile(zip_fp or (zip_data and StringIO(zip_data)) or open(zip_filepath, "rb"))
    z.extractall(os.path.join(settings.USER_WRITABLE_LOCALE_DIR, lang_code))

def move_dubbed_video_map(lang_code):
    lang_pack_location = os.path.join(settings.USER_WRITABLE_LOCALE_DIR, lang_code)
    dubbed_video_dir = os.path.join(lang_pack_location, "dubbed_videos")
    dvm_filepath = os.path.join(dubbed_video_dir, os.path.basename(settings.DUBBED_VIDEOS_MAPPING_FILEPATH))
    if not os.path.exists(dvm_filepath):
        logging.error("Could not find downloaded dubbed video filepath: %s" % dvm_filepath)
    else:
        logging.debug("Moving dubbed video map to %s" % settings.DUBBED_VIDEOS_MAPPING_FILEPATH)
        ensure_dir(os.path.dirname(settings.DUBBED_VIDEOS_MAPPING_FILEPATH))
        shutil.move(dvm_filepath, settings.DUBBED_VIDEOS_MAPPING_FILEPATH)

        logging.debug("Removing empty directory")
        try:
            shutil.rmtree(dubbed_video_dir)
        except Exception as e:
            logging.error("Error removing dubbed video directory (%s): %s" % (dubbed_video_dir, e))

def move_video_sizes_file(lang_code):
    lang_pack_location = os.path.join(settings.USER_WRITABLE_LOCALE_DIR, lang_code)
    filename = os.path.basename(REMOTE_VIDEO_SIZE_FILEPATH)
    src_path = os.path.join(lang_pack_location, filename)
    dest_path = REMOTE_VIDEO_SIZE_FILEPATH

    # replace the old remote_video_size json
    if not os.path.exists(src_path):
        logging.error("Could not find videos sizes file (%s)" % src_path)
    else:
        logging.debug('Moving %s to %s' % (src_path, dest_path))
        shutil.move(src_path, dest_path)

def move_exercises(lang_code):
    lang_pack_location = os.path.join(settings.USER_WRITABLE_LOCALE_DIR, lang_code)
    src_exercise_dir = os.path.join(lang_pack_location, "exercises")
    dest_exercise_dir = get_localized_exercise_dirpath(lang_code)

    if not os.path.exists(src_exercise_dir):
        logging.warn("Could not find downloaded exercises; skipping: %s" % src_exercise_dir)
    else:
        # Move over one at a time, to combine with any other resources that were there before.
        ensure_dir(dest_exercise_dir)
        all_exercise_files = glob.glob(os.path.join(src_exercise_dir, "*.html"))
        logging.info("Moving %d downloaded exercises to %s" % (len(all_exercise_files), dest_exercise_dir))

        for exercise_file in all_exercise_files:
            shutil.move(exercise_file, os.path.join(dest_exercise_dir, os.path.basename(exercise_file)))

        logging.debug("Removing emtpy directory")
        try:
            shutil.rmtree(src_exercise_dir)
        except Exception as e:
            logging.error("Error removing dubbed video directory (%s): %s" % (src_exercise_dir, e))

def move_srts(lang_code):
    """
    Srts live in the locale directory, but that's not exposed at any URL.  So instead,
    we have to move the srts out to /static/subtitles/[lang_code]/
    """
    lang_code_ietf = lcode_to_ietf(lang_code)
    lang_code_django = lcode_to_django_dir(lang_code)

    subtitles_static_dir = os.path.join(settings.USER_STATIC_FILES, "subtitles")
    src_dir = os.path.join(settings.USER_WRITABLE_LOCALE_DIR, lang_code_django, "subtitles")
    dest_dir = get_srt_path(lang_code_django)
    ensure_dir(dest_dir)

    lang_subtitles = glob.glob(os.path.join(src_dir, "*.srt"))
    logging.info("Moving %d subtitles from %s to %s" % (len(lang_subtitles), src_dir, dest_dir))

    for fil in lang_subtitles:
        srt_dest_path = os.path.join(dest_dir, os.path.basename(fil))
        if os.path.exists(srt_dest_path):
            os.remove(srt_dest_path)  # we're going to replace any srt with a newer version
        shutil.move(fil, srt_dest_path)

    if not os.path.exists(src_dir):
        logging.info("No subtitles for language pack %s" % lang_code)
    elif os.listdir(src_dir):
        logging.warn("%s is not empty; will not remove.  Please check that all subtitles were moved." % src_dir)
    else:
        logging.info("Removing empty source directory (%s)." % src_dir)
        shutil.rmtree(src_dir)
