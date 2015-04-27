import subprocess
import sys
from django.core.management.base import NoArgsCommand


class Command(NoArgsCommand):

    def handle_noargs(self, **options):

        subprocess.call(["git", "--no-pager", "grep", "\# TODO"])

        print '''

        Checking if we have TODO-BLOCKERS...

        '''

        ret = subprocess.call(["git", "--no-pager", "grep", "\#.*TODO-BLOCKER"])

        sys.exit(not ret)       # if we have todo-blockers, error out
