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
		make_option('--new_po', '-n', dest='new_po', action="store_true", default=False, help='Running with -n will run the makemessages command to generate new po files.'),
		make_option('--post_po', '-p', dest='post_po', action="store_true", default=False, help='Running with -p will copy the current po files to the static url so that they can be inserted into CrowdIn.'),
	)
	help = 'Po management commands. See options for usage help.'

	def handle(self, **options):

		if options.get("new_po"):
			generate_new_po_files()
		if options.get("post_po"):
			# check_po_files() -- check them for asterisks before posting them - another great hackathon project!
			post_po_files()
		if options.get("test_wrappings"):
			generate_test_files()

def generate_new_po_files():
	"""Run makemessages on relevant parts of codebase to create new po files"""
	# Change to project root dir
	project_root = os.path.join(settings.PROJECT_PATH, "../")
	os.chdir(project_root)
	ensure_dir(os.path.join(project_root, "locale/"))

	# Generate english po file
	ignore_pattern = ['python-packages/*']
	management.call_command('makemessages', locale='en', ignore_patterns=ignore_pattern, no_obsolete=True)
	# Generate english po file for javascript
	ignore_pattern = ['kalite/static/admin/js/*', 'python-packages/*']
	management.call_command('makemessages', domain='djangojs', locale='en', ignore_patterns=ignore_pattern, no_obsolete=True)


def post_po_files():
	"""Copy current po files into static dir (which is be exposed for download)""" 
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
