"""
"""
import os
import sys

from django.core.management.base import NoArgsCommand
from django.conf import settings

from behave.__main__ import main as behave_main


class Command(NoArgsCommand):

    def handle_noargs(self, **options):
        cmd = None
       
        # Run the behave tests
        # Act like we're invoking behave from the command line.
        sys.argv = []
        sys.argv.append("behave")
        
        # Get all directories with a "steps" subdirectory,
        # since this is what "behave" expects
        def visit(arg, dirname, names):
            if "steps" in names:
                sys.argv.append(dirname)
        
        os.path.walk(settings.PROJECT_PATH, visit, None)

        behave_main()
