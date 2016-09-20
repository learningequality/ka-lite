import os
import shutil
import tempfile
import zipfile

from optparse import make_option

from django.conf import settings as django_settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils.translation import ugettext as _

from fle_utils.general import ensure_dir

from kalite.contentload import settings as content_settings
from kalite.i18n.base import lcode_to_django_lang, get_po_filepath, get_locale_path, \
    download_content_pack, update_jsi18n_file, get_subtitle_file_path as get_subtitle_path, \
    extract_content_db, get_localized_exercise_dirpath
from kalite.updates.management.utils import UpdatesStaticCommand

logging = django_settings.LOG


class Command(UpdatesStaticCommand):
    """
    Management command for downloading a language pack and extracting the
    contents to their correct locations.

    Usage:
    kalite manage retrievecontentpack download <lang>
    kalite manage retrievecontentpack local <lang> <packpath>
    kalite manage retrievecontentpack -h | --help

    """

    option_list = UpdatesStaticCommand.option_list + (
        make_option(
            "", "--minimal",
            action="store_true",
            dest="minimal",
            default=False,
            help=(
                "0.16 legacy: Try fetching a minimal version of the content "
                "pack without assessment items."
            )
        ),
        make_option(
            "", "--template",
            action="store_true",
            dest="template",
            default=False,
            help=(
                "Extract contents of the content pack into template "
                "directories which source distribution uses to bundle in "
                "content db's (and nothing more at the moment)"
            ),
        ),
    )

    help = __doc__

    stages = (
        "retrieve_language_pack",
        "extract_files",
        "check_availability",
    )

    def handle(self, *args, **options):

        self.setup(options)

        operation = args[0]
        self.minimal = options.get('minimal', False)
        self.foreground = options.get('foreground', False)
        self.is_template = options.get('template', False)

        if self.is_template:
            ensure_dir(django_settings.DB_CONTENT_ITEM_TEMPLATE_DIR)

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
            zf = download_content_pack(f, lang, minimal=self.minimal)
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
        extract_content_db(zf, lang, is_template=self.is_template)
        extract_subtitles(zf, lang)
        extract_content_pack_metadata(zf, lang)  # always extract to the en lang
        extract_assessment_items(zf, "en")
        extract_html_exercises(zf, lang)

        if not self.is_template:
            self.next_stage(_("Looking for available content items."))
            call_command("annotate_content_items", language=lang)

        self.complete(_("Finished processing content pack."))


def extract_html_exercises(zf, lang):
    exercise_dest_path = get_localized_exercise_dirpath(lang)
    zip_exercise_path = "exercises/"

    items = [s for s in zf.namelist() if zip_exercise_path in s]

    if not items:  # no html exercises to extract
        return

    extract_path = tempfile.mkdtemp()
    full_extract_path = os.path.join(extract_path, zip_exercise_path)
    try:
        zf.extractall(extract_path, items)

        shutil.rmtree(exercise_dest_path, ignore_errors=True)
        shutil.move(full_extract_path, exercise_dest_path)
    finally:                    # no matter what happens, remove the extract path
        shutil.rmtree(extract_path)


def extract_content_pack_metadata(zf, lang):
    metadata_path = os.path.join(get_locale_path(lang), "{lang}_metadata.json".format(lang=lang))
    pack_metadata_name = "metadata.json"

    with open(metadata_path, "wb") as f, zf.open(pack_metadata_name) as mf:
        shutil.copyfileobj(mf, f)


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
    items = (s for s in zf.namelist() if assessment_zip_dir in s)
    zf.extractall(content_settings.ASSESSMENT_ITEM_ROOT, items)
