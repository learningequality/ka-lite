import os

from django.core.management import call_command
from optparse import make_option

from django.conf import settings as django_settings
logging = django_settings.LOG

from kalite.topic_tools.content_models import annotate_content_models

from kalite.topic_tools.settings import CONTENT_DATABASE_PATH

from kalite.updates.management.commands.classes import UpdatesStaticCommand

from django.utils.translation import gettext as _


class Command(UpdatesStaticCommand):

    option_list = UpdatesStaticCommand.option_list + (
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

    stages = (
        "annotate_content_models",
    )

    def handle(self, *args, **kwargs):

        language = kwargs["language"]
        channel = kwargs["channel"]
        # temporarily swap out the database path for the desired target
        database_path = kwargs["database_path"] or CONTENT_DATABASE_PATH.format(channel=channel, language=language)

        self.start(_("Annotating content for language: {language}, channel: {channel}").format(
            language=language,
            channel=channel))
        annotate_content_models(database_path=database_path, channel=channel, language=language)

        self.complete(_("Annotation complete for language: {language}, channel: {channel}").format(
            language=language,
            channel=channel))
