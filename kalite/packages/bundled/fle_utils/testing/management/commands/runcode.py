import copy
import json

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    args = "<code_to_run>"

    help = "Runs arbitrary code in the context of the Django app."

    def handle(self, *args, **options):

        if len(args) == 0:
            raise CommandError("No code specified")

        existing_vars = copy.copy(locals().keys() + ["existing_vars"])

        exec(" ".join(args))

        results = copy.copy(locals())

        for key in existing_vars:
            results.pop(key)

        for key, val in results.items():
            try:
                json.dumps(val)
            except:
                results.pop(key)

        self.stdout.write(json.dumps(results))