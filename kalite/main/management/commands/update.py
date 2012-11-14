from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from sh import git

class Command(BaseCommand):
    help = "Pull from the git repository and do a syncdb/migrate."

    def handle(self, *args, **options):
        self.run(git, "pull")
        call_command("syncdb")
        call_command("migrate", merge=True)
        self.stdout.write("Update is complete!\n")

    def run(self, command, *args, **kwargs):
        results = command(*args, **kwargs)
        if results.stdout:
            self.stdout.write(results.stdout)
        if results.stderr:
            self.stderr.write(results.stderr)
        return results