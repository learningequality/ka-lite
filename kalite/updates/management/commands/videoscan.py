from kalite.updates.management.utils import UpdatesStaticCommand
from optparse import make_option

from django.core.management import call_command

from django.utils.translation import gettext as _


class Command(UpdatesStaticCommand):

    option_list = UpdatesStaticCommand.option_list + (
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

        self.setup(kwargs)

        language = kwargs["language"]
        channel = kwargs["channel"]

        self.start(_("Annotating content for language: {language}, channel: {channel}").format(
            language=language,
            channel=channel))
        call_command("annotate_content_items", channel=channel, language=language, verbosity=0)

        self.complete(_("Annotation complete for language: {language}, channel: {channel}").format(
            language=language,
            channel=channel))
