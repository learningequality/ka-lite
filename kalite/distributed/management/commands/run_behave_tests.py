"""
"""
import sys

from django.conf import settings
from django.core.management.base import NoArgsCommand
from django.core.management import call_command

from behave.__main__ import main

class Command(NoArgsCommand):

    def handle_noargs(self, **options):
        cmd = None
    
        sys.argv = []
        sys.argv.append("behave")
        sys.argv.append("/home/gallaspy/Desktop/ka-lite/kalite/distributed/tests/features")
        main()
