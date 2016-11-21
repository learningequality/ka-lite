import glob
import json
import os
import requests

from optparse import make_option

from django.conf import settings as django_settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from kalite.topic_tools.content_models import Item, set_database, parse_data, AssessmentItem

from kalite.i18n.base import get_locale_path, get_subtitle_file_path as get_subtitle_path, \
    get_localized_exercise_dirpath

from kalite.version import SHORTVERSION

logging = django_settings.LOG


class Command(BaseCommand):
    """
    Management command for inspecting a language pack that has been installed locally,
    and reporting a number of statistics about it.

    Include `--update` to update the language pack(s) before printing the results.
    Note that <lang> is a language code, or "all" to run for all languages.

    Usage:
    kalite manage contentpackchecker <lang> [--update]
    """

    option_list = BaseCommand.option_list + (
        make_option('--update',
            action='store_true',
            dest='update',
            default=False,
            help='',
        ),
    )

    help = __doc__

    def handle(self, *args, **options):

        if len(args) == 0:
            print self.help
            return

        languages = [args[0]]

        if languages[0] == "all":

            metadata_url = "https://learningequality.org/downloads/ka-lite/{version}/content/contentpacks/all_metadata.json".format(version=SHORTVERSION)

            metadata = json.loads(requests.get(metadata_url).content)

            languages = [lang["code"] for lang in metadata]

        if options["update"]:
            for language in languages:
                call_command("retrievecontentpack", "download", language)

        for language in languages:

            print ""

            print "STATS FOR LANGUAGE {language}:".format(language=language)

            print ""

            try:
                print "\tMetadata:"
                for key, val in self.get_content_pack_metadata(language).items():
                    print "\t\t{key}: {val}".format(key=key, val=val)
            except IOError:
                print "\t\tDOES NOT EXIST!"
                continue

            print ""

            print "\tNumber of topics:", len(self.get_content_items_by_kind(language=language, kind="Topic"))
            print "\tNumber of videos:", len(self.get_content_items_by_kind(language=language, kind="Video"))
            print "\tNumber of unique videos:", len(set([item["youtube_id"] for item in self.get_content_items_by_kind(language=language, kind="Video")]))
            print "\tNumber of exercises:", len(self.get_content_items_by_kind(language=language, kind="Exercise"))
            print "\tNumber of unique exercises:", len(set([item["id"] for item in self.get_content_items_by_kind(language=language, kind="Exercise")]))
            print "\tNumber of assessment items:", self.count_assessment_items(language=language)

            print "\tNumber of khan-exercises files:", len(self.get_html_exercises(language=language))
            print "\tNumber of subtitle files:", len(self.get_subtitles(language=language))

            print ""

    @parse_data
    @set_database
    def get_content_items_by_kind(self, kind, **kwargs):
        return Item.select().where(Item.kind == kind)

    @set_database
    def count_assessment_items(self, **kwargs):
        return AssessmentItem.select().count()

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
