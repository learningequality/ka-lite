import json

from django.core.management.base import NoArgsCommand
from django.core.management import call_command

from django.dispatch import receiver

from compressor.signals import post_compress

class Command(NoArgsCommand):
    """
    This command wraps the django compressor 'compress' command in order to allow us to
    construct a json file with a mapping from js and css block names to file names.
    This is required in order to reference the files in proper order for inclusion in Javascript
    Unit Tests.
    """

    def handle_noargs(self, **options):

        call_command("collectstatic", interactive=False)

        manifest = {}

        @receiver(post_compress)
        def handle_post_compress(sender, **kwargs):
            manifest[kwargs.get("context").get("compressed").get("name")] = kwargs.get("context").get("compressed").get("url")

        call_command("compress", force=True)

        with open("file_map.json", "w") as f:
            json.dump(manifest, f)
