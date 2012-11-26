from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
import git

class Command(BaseCommand):
    help = "Pull from the git repository and do a syncdb/migrate."

    def handle(self, *args, **options):
        self.stdout.write(git.Repo(".").git.pull() + "\n")
        call_command("syncdb", migrate=True)
        self.stdout.write("Update is complete!\n")
    