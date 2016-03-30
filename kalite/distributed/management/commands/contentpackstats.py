import glob
import json
import os
import shutil
import tempfile
import zipfile

from optparse import make_option

from django.conf import settings as django_settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext as _

from fle_utils.general import ensure_dir

from kalite.topic_tools.content_models import get_content_items, Item, set_database, parse_data

from kalite.i18n.base import lcode_to_django_lang, get_po_filepath, get_locale_path, \
    download_content_pack, update_jsi18n_file, get_subtitle_file_path as get_subtitle_path, \
    extract_content_db, get_localized_exercise_dirpath

logging = django_settings.LOG


class Command(BaseCommand):
    """
    Management command for inspecting a language pack that has been installed locally,
    and reporting a number of statistics about it.

    Usage:
    kalite manage contentpackstats <lang>
    """

    help = __doc__

    def handle(self, *args, **options):

        if len(args) == 0:
            print self.help
            return

        language = args[0]

        print "Number of videos:", len(self.get_content_items_by_kind(language=language, kind="Video"))
        print "Number of exercises:", len(self.get_content_items_by_kind(language=language, kind="Exercise"))
        print "Number of topics:", len(self.get_content_items_by_kind(language=language, kind="Topic"))

        print "Number of khan-exercises files:", len(self.get_html_exercises(language=language))
        print "Number of subtitle files:", len(self.get_subtitles(language=language))

        print ""

        print "Metadata:"
        for key, val in self.get_content_pack_metadata(language).items():
            print "\t{key}: {val}".format(key=key, val=val)

    @parse_data
    @set_database
    def get_content_items_by_kind(self, kind, **kwargs):
        return Item.select().where(Item.kind == kind)

    def get_html_exercises(self, language):
        exercise_dest_path = get_localized_exercise_dirpath(language)
        return glob.glob(os.path.join(exercise_dest_path, "*.html"))


    def get_content_pack_metadata(self, language):
        metadata_path = os.path.join(get_locale_path(language), "{language}_metadata.json".format(language=language))

        with open(metadata_path) as f:
            metadata = json.load(f)

        return metadata


    def get_subtitles(self, language):
        SUBTITLE_DEST_DIR = get_subtitle_path(lang_code=language)

        return glob.glob(os.path.join(SUBTITLE_DEST_DIR, "*.vtt"))



# def extract_assessment_items(zf, lang):
#     assessment_zip_dir = "khan/"
#     items = (s for s in zf.namelist() if assessment_zip_dir in s)
#     zf.extractall(content_settings.ASSESSMENT_ITEM_ROOT, items)
