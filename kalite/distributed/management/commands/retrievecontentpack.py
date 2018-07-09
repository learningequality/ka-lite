import logging
import os
import shutil
import socket
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
    extract_content_db
from kalite.topic_tools import settings as topic_settings
from kalite.updates.management.utils import UpdatesStaticCommand
from peewee import SqliteDatabase
from kalite.topic_tools.content_models import Item, AssessmentItem
from requests.exceptions import ConnectionError, HTTPError
from fle_utils.django_utils.command import LocaleAwareCommand


logger = logging.getLogger(__name__)


class Command(UpdatesStaticCommand):
    """
    Management command for downloading a language pack and extracting the
    contents to their correct locations.

    Usage:
    kalite manage retrievecontentpack download <lang>
    kalite manage retrievecontentpack empty <lang>
    kalite manage retrievecontentpack local <lang> <packpath>
    kalite manage retrievecontentpack -h | --help

    """


    option_list = LocaleAwareCommand.option_list + (
        make_option(
            "", "--background",
            action="store_true",
            dest="background",
            default=False,
            help=(
                "Run the command with job scheduler and database-backed "
                "progress. Used when you retrieve a content pack before "
                "initializing KA Lite's db."
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
        make_option(
            "-f", "--force",
            action="store_true",
            dest="force",
            default=False,
            help=(
                "Overwrite existing user data if it exists."
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
        self.foreground = options.get('foreground', False)
        self.is_template = options.get('template', False)
        self.force = options.get('force', False)

        if self.is_template:
            ensure_dir(django_settings.DB_CONTENT_ITEM_TEMPLATE_DIR)
        
        # This is sort of undefined, because templates are always assumed fine
        # to overwrite
        if self.is_template and self.force:
            raise CommandError("Cannot combine --force and --template.")

        if operation == "download":
            self.start(_("Downloading content pack."))
            self.download(*args, **options)
        elif operation == "local":
            self.start(_("Installing a local content pack."))
            self.local(*args, **options)
        elif operation == "empty":
            self.empty(*args, **options)
        else:
            raise CommandError("Unknown operation: %s" % operation)

    def empty(self, *args, **options):
        """
        Creates an empty content database for the Khan channel. This ensures
        that an empty content database exists in the default distribution and
        for tests.
        
        Especially useful for creating an *EMPTY TEMPLATE*
        
        retrievecontentpack empty en --template
        """
        lang = args[1]
        if not options.get('template', False):
            content_db_path = topic_settings.CONTENT_DATABASE_PATH.format(
                channel=topic_settings.CHANNEL,
                language=lang,
            )
        else:
            content_db_path = topic_settings.CONTENT_DATABASE_TEMPLATE_PATH.format(
                channel=topic_settings.CHANNEL,
                language=lang,
            )
        if os.path.exists(content_db_path):
            if options.get("force", False):
                os.unlink(content_db_path)
            else:
                raise CommandError(
                    "Content database already exists: {}".format(
                        content_db_path
                    )
                )
        db = SqliteDatabase(
            content_db_path
        )
        db.connect()
        db.create_table(Item, safe=True)
        db.create_table(AssessmentItem, safe=True)
        db.close()
        self.complete(
            _("Saved empty content database in {}.").format(
                content_db_path
            )
        )

    def download(self, *args, **options):

        lang = args[1]

        # This rather hacky callback will add progress to the database-backed
        # progress monitoriing, which is terrible for performance on for
        # instance Raspberry Pi devices.
        def download_callback(fraction):
            percent = int(fraction * 100)
            self.update_stage(
                fraction,
                stage_status=_("Downloaded {pct}% of {lang} content pack").format(
                    pct=percent,
                    lang=lang,
                )
            )

        with tempfile.NamedTemporaryFile() as f:
            try:
                zf = download_content_pack(f, lang, callback=download_callback)
            except (socket.error, ConnectionError, HTTPError) as e:
                self.cancel("Could not download content pack, unable to connect", str(e))
                return
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

        if not self.is_template:
            self.next_stage(_("Looking for available content items."))
            call_command("annotate_content_items", language=lang)

        self.complete(_("Finished processing content pack."))


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
        logger.debug("writing to %s" % mopath)
        with open(mopath, "wb") as djangomof:
            shutil.copyfileobj(zipmof, djangomof)


def extract_subtitles(zf, lang):
    SUBTITLE_DEST_DIR = get_subtitle_path(lang_code=lang)
    SUBTITLE_ZIP_DIR = "subtitles/"

    ensure_dir(SUBTITLE_DEST_DIR)

    def is_subtitle_file(s):
        return SUBTITLE_ZIP_DIR in s and len(s) > len(SUBTITLE_ZIP_DIR)

    subtitles = (s for s in zf.namelist() if is_subtitle_file(s))

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
