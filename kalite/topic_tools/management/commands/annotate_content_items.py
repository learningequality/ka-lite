from optparse import make_option

from django.conf import settings as django_settings
from django.core.management.base import BaseCommand
from kalite.topic_tools.content_models import annotate_content_models
from kalite.topic_tools.settings import CONTENT_DATABASE_PATH


logging = django_settings.LOG


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option("-d", "--database-path",
                    action="store",
                    dest="database_path",
                    default="",
                    help="Override the destination path for the content item DB file"),
        make_option("-c", "--channel",
                    action="store",
                    dest="channel",
                    default="khan",
                    help="Channel to annotate database for."),
        make_option("-l", "--language",
                    action="store",
                    dest="language",
                    default="en",
                    help="Language to annotate database for."),
    )

    def handle(self, *args, **kwargs):

        language = kwargs["language"]
        channel = kwargs["channel"]
        # temporarily swap out the database path for the desired target
        database_path = kwargs["database_path"] or CONTENT_DATABASE_PATH.format(channel=channel, language=language)

        logging.info(
            (
                "Annotating content for language: {language}, channel: {channel}\n\n"
                "This may take several minutes depending on system resources..."
            ).format(
                language=language,
                channel=channel
            )
        )
        annotate_content_models(database_path=database_path, channel=channel, language=language)

        logging.info("Annotation complete for language: {language}, channel: {channel}".format(
            language=language,
            channel=channel))
