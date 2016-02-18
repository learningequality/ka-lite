import os
import urllib
import tempfile
import shutil
import zipfile

from django.core.management.base import CommandError
from django.core.management import call_command
from django.utils.translation import ugettext as _

from django.conf import settings as django_settings
logging = django_settings.LOG

from fle_utils.general import ensure_dir

from kalite.contentload import settings as content_settings
from kalite.i18n.base import lcode_to_django_lang, get_po_filepath, get_locale_path, \
    update_jsi18n_file, get_srt_path as get_subtitle_path
from kalite.topic_tools import settings
from kalite.updates.management.commands.classes import UpdatesStaticCommand

from kalite.version import SHORTVERSION

CONTENT_PACK_URL_TEMPLATE = ("http://pantry.learningequality.org/downloads"
                             "/ka-lite/{version}/content/contentpacks/{code}.zip")


class Command(UpdatesStaticCommand):
    """
    Management command for downloading a language pack and extracting the
    contents to their correct locations.

    Usage:
    kalite manage retrievecontentpack download <lang>
    kalite manage retrievecontentpack local <lang> <packpath>
    kalite manage retrievecontentpack -h | --help

    """

    help = __doc__

    stages = (
        "retrieve_language_pack",
        "extract_files",
        "check_availability",
    )

    def handle(self, *args, **options):

        operation = args[0]

        if operation == "download":
            self.start(_("Downloading content pack."))
            self.download(*args, **options)
        elif operation == "local":
            self.start(_("Installing a local content pack."))
            self.local(*args, **options)
        else:
            raise CommandError("Unknown operation: %s" % operation)

    def download(self, *args, **options):

        lang = args[1]

        with tempfile.NamedTemporaryFile() as f:
            zf = download_content_pack(f, lang)
            self.process_content_pack(zf, lang)
            zf.close()

    def local(self, *args, **options):

        lang = args[1]
        zippath = args[2]

        assert os.path.isfile(zippath), "%s doesn't seem to be a file." % zippath

        with zipfile.ZipFile(zippath) as zf:
            self.process_content_pack(zf, lang)

    def process_content_pack(self, zf, lang):

        self.next_stage(_("Moving content files to the right place."))
        extract_catalog_files(zf, lang)
        update_jsi18n_file(lang)
        extract_content_db(zf, lang)
        extract_subtitles(zf, lang)
        extract_content_pack_metadata(zf, lang) # always extract to the en lang
        extract_assessment_items(zf, "en")

        self.next_stage(_("Looking for available content items."))
        call_command("annotate_content_items", language=lang)

        self.complete(_("Finished processing content pack."))


def extract_content_pack_metadata(zf, lang):
    metadata_path = os.path.join(get_locale_path(lang), "{lang}_metadata.json".format(lang=lang))
    pack_metadata_name = "metadata.json"

    with open(metadata_path, "wb") as f, zf.open(pack_metadata_name) as mf:
        shutil.copyfileobj(mf, f)


def download_content_pack(fobj, lang):
    url = CONTENT_PACK_URL_TEMPLATE.format(
        version=SHORTVERSION,
        code=lang,
    )

    httpf = urllib.urlopen(url)  # returns a file-like object not exactly to zipfile's liking, so save first

    shutil.copyfileobj(httpf, fobj)
    fobj.seek(0)
    zf = zipfile.ZipFile(fobj)

    httpf.close()

    return zf


def extract_catalog_files(zf, lang):
    lang = lcode_to_django_lang(lang)
    modir = get_po_filepath(lang)
    ensure_dir(modir)

    filename_mapping = {"frontend.mo": "djangojs.mo",
                        "backend.mo": "django.mo"}

    for zipmo, djangomo in filename_mapping.items():
        zipmof = zf.open(zipmo)
        mopath = os.path.join(modir, djangomo)
        logging.debug("writing to %s" % mopath)
        with open(mopath, "wb") as djangomof:
            shutil.copyfileobj(zipmof, djangomof)


def extract_content_db(zf, lang):
    content_db_path = settings.CONTENT_DATABASE_PATH.format(
        channel=settings.CHANNEL,
        language=lang,
    )

    with open(content_db_path, "wb") as f:
        dbfobj = zf.open("content.db")
        shutil.copyfileobj(dbfobj, f)


def extract_subtitles(zf, lang):
    SUBTITLE_DEST_DIR = get_subtitle_path(lang_code=lang)
    SUBTITLE_ZIP_DIR = "subtitles/"

    ensure_dir(SUBTITLE_DEST_DIR)

    subtitles = (s for s in zf.namelist() if SUBTITLE_ZIP_DIR in s)

    for subtitle in subtitles:
        # files inside zipfiles may come with leading directories in their
        # names, like subtitles/hotdog.vtt. We'll only want the actual filename
        # (hotdog.vtt) when extracting as that's what KA Lite expects.

        subtitle_filename = os.path.basename(subtitle)
        subtitle_dest_path = os.path.join(SUBTITLE_DEST_DIR, subtitle_filename)

        subtitle_fileobj = zf.open(subtitle)

        with open(subtitle_dest_path, "w") as dest_fileobj:
            shutil.copyfileobj(subtitle_fileobj, dest_fileobj)


def extract_assessment_items(zf, lang):
    assessment_zip_dir = "khan/"
    assessment_dest_dir = os.path.join(content_settings.ASSESSMENT_ITEM_ROOT)

    _extract_assessment_resources(zf, assessment_zip_dir, assessment_dest_dir)


def _extract_assessment_resources(zf, assessment_zip_dir, assessment_dest_dir):
    items = (s for s in zf.namelist() if assessment_zip_dir in s)

    zf.extractall(assessment_dest_dir, items)
