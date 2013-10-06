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
		make_option('--test', '-t', dest='test_wrappings', action="store_true", default=False, help='Running with -t will fill in current po files msgstrs with asterisks. This will allow you to quickly identify unwrapped strings in the codebase and wrap them in translation tags! Remember to delete after your finished testing.'),
	)
	help = 'USAGE: \'python manage.py update_po\' defaults to creating new template files. If run with -t, will generate test po files that make it easy to identify strings that need wrapping.'

	def handle(self, **options):
		if options.get("test_wrapping"):
			generate_test_files()
		else:
			update_templates()
			
def move_to_project_root():
	"""Change into the project root directory to run i18n commands"""
	project_root = os.path.join(settings.PROJECT_PATH, "../")
	os.chdir(project_root)
	ensure_dir(os.path.join(project_root, "locale/"))


def update_templates():
	"""Update template po files"""
	## Command must be run from project root
	move_to_project_root()

	## delete current english locale directories if they exist to prevent any translations from being uploaded (safety measure)
	english_path = os.path.join(settings.LOCALE_PATHS[0], "en")
	if os.path.exists(english_path):
		shutil.rmtree(english_path)

	## generate new files
	# Generate english po file
	ignore_pattern = ['python-packages/*']
	management.call_command('makemessages', locale='en', ignore_patterns=ignore_pattern, no_obsolete=True)
	# Generate english po file for javascript
	ignore_pattern = ['kalite/static/admin/js/*', 'python-packages/*']
	management.call_command('makemessages', domain='djangojs', locale='en', ignore_patterns=ignore_pattern, no_obsolete=True)
	
	## post them to exposed URL
	static_path = os.path.join(settings.STATIC_ROOT, "pot/")
	ensure_dir(static_path)
	shutil.copy(os.path.join(settings.LOCALE_PATHS[0], "en/LC_MESSAGES/django.po"), os.path.join(static_path, "kalite.pot"))
	shutil.copy(os.path.join(settings.LOCALE_PATHS[0], "en/LC_MESSAGES/djangojs.po"), os.path.join(static_path, "kalitejs.pot"))


def generate_test_files():
	"""Insert asterisks as translations in po files"""
	# A great hackathon project!!
	# (hopefully) helpful outline: you'll probably need to open up the po files, read through them, extract any variables, and insert 
	# asterisks and variables into the msgstr. 
	return True

