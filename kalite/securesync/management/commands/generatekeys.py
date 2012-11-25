from django.core.management.base import BaseCommand, CommandError
from securesync.crypto import reset_keys
from config.models import Settings

class Command(BaseCommand):
    help = "Generate a new public/private keypair"

    def handle(self, *args, **options):
        if Settings.get("private_key"):
            self.stderr.write("Error: This device already has a private/public keypair generated for it; aborting.\n")
            return
        self.stdout.write("Generating 2048-bit RSA public/private keys...\n")
        reset_keys()
        self.stdout.write("Done!\n")
        