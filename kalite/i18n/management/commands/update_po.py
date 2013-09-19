"""
Update po files, write them to exposed URL.
"""

import os
import shutil

from optparse import make_option
from django.core import management
from django.core.management.base import BaseCommand, CommandError

import settings
from utils.general import ensure_dir

class Command(BaseCommand):
	option_list = BaseCommand.option_list + (
		# make_option('--verbose', '-v', dest='', help=''),
	)
	help = 'Run command to generate a fresh pot file and expose it via the central/api.'

	def handle(self, **options):
		# Change to project root dir
		os.chdir(os.path.join(settings.PROJECT_PATH, "../"))
		# Generate english po file
		management.call_command('makemessages', locale='en')
		# Generate english po file from javascript
		management.call_command('makemessages', domain='djangojs', locale='en')

		# cp new files into static dir (which should be exposed for download) 
		static_path = os.path.join(settings.STATIC_ROOT, "pot/")
		ensure_dir(static_path)
		shutil.copy(os.path.join(settings.LOCALE_PATHS[0], "en/LC_MESSAGES/django.po"), os.path.join(static_path, "kalite.pot"))
		shutil.copy(os.path.join(settings.LOCALE_PATHS[0], "en/LC_MESSAGES/djangojs.po"), os.path.join(static_path, "kalitejs.pot"))