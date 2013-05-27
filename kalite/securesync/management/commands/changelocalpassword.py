import getpass
import os
import random
import string
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS

import settings
from securesync.models import FacilityUser


def generate_random_password(length=10, charset=(string.ascii_letters + string.digits + '!@#$%^&*()')):
    random.seed = (os.urandom(1024))

    return ''.join(random.choice(charset) for i in range(length))
    

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--database', action='store', dest='database',
            default=DEFAULT_DB_ALIAS, help='Specifies the database to use. Default is "default".'),
        make_option('--noinput', action='store_true', dest='noinput',
            default=False, help='Generate a new password (10 characters)'),
    )
    help = "Change a LOCAL KA Lite facility user's password"

    requires_model_validation = False

    def _get_pass(self, prompt="Password: "):
        p = getpass.getpass(prompt=prompt)
        if not p:
            raise CommandError("aborted")
        return p

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("need exactly one argument (username)")

        if args:
            username, = args

        try:
            u = FacilityUser.objects.using(options.get('database')).get(username=username)
        except FacilityUser.DoesNotExist:
            raise CommandError("user '%s' does not exist" % username)

        self.stdout.write("Changing password for user '%s'\n" % u.username)

        if options['noinput']:
            p1 = generate_random_password()
            self.stdout.write("Generated new password for user '%s': '%s'\n" % (username, p1))
            
        else:
            MAX_TRIES = 3
            count = 0
            p1, p2 = 1, 2  # To make them initially mismatch.
            while p1 != p2 and count < MAX_TRIES:
                p1 = self._get_pass()
                p2 = self._get_pass("Password (again): ")
                if p1 != p2:
                    self.stdout.write("Passwords do not match. Please try again.\n")
                    count = count + 1

            if count == MAX_TRIES:
                raise CommandError("Aborting password change for user '%s' after %s attempts" % (username, count))

        u.set_password(p1)
        u.save()

        return "Password changed successfully for user '%s'\n" % u.username
