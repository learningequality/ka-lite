"""
"""
from django.core.management.base import BaseCommand, CommandError

from ...crypto import reset_keys
from fle_utils.config.models import Settings


class Command(BaseCommand):
    help = "Generate a new public/private keypair"

    def handle(self, *args, **options):
        if Settings.get("private_key"):
            self.stderr.write("Error: This device already has an encryption key generated for it; aborting.\n")
            return
        self.stdout.write("Generating 2048-bit RSA encryption key (may take a few minutes; please wait)...\n")
        reset_keys()
        self.stdout.write("Done!\n")
