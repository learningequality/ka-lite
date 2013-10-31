"""
This command automates the process of generating template po files, which can be uploaded to crowdin. 
It runs the django commands makemessages and compilemessages and moves the created files to an 
exposed url, so that they can be downloaded from the web by KA's scripts.

It has an optional flag, -t, which inserts asterisks around the strings in the po files, and 
compiles them, so that when you run the server, English has been translated to *English* in the 
hope of making it easy to identify unwrapped strings.

This can be run independently of cache_translations
"""

import re
import os
import shutil

from optparse import make_option
from django.core import management
from django.core.management.base import BaseCommand, CommandError

import settings
from settings import LOG as logging
from utils.django_utils import call_command_with_output
from utils.general import ensure_dir

class Command(BaseCommand):
	option_list = BaseCommand.option_list + (
		make_option('--test', '-t', dest='test_wrappings', action="store_true", default=False, help='Running with -t will fill in current po files msgstrs with asterisks. This will allow you to quickly identify unwrapped strings in the codebase and wrap them in translation tags! Remember to delete after your finished testing.'),
	)
	help = 'USAGE: \'python manage.py update_po\' defaults to creating new template files. If run with -t, will generate test po files that make it easy to identify strings that need wrapping.'

	def handle(self, **options):
		## All commands must be run from project root
		move_to_project_root()
		## (safety measure) prevent any english or test translations from being uploaded 
		delete_current_templates()

		## Create new files 
		run_makemessages()

		## Handle flags
		if options.get("test_wrappings"):
			generate_test_files()
		else:
			update_templates()
			
def move_to_project_root():
	"""Change into the project root directory to run i18n commands"""
	logging.info("Moving to project root directory")
	project_root = os.path.join(settings.PROJECT_PATH, "../")
	os.chdir(project_root)
	ensure_dir(os.path.join(project_root, "locale/"))


def delete_current_templates():
	"""Delete existing en po files"""
	logging.info("Deleting English language locale directory")
	english_path = os.path.join(settings.LOCALE_PATHS[0], "en")
	if os.path.exists(english_path):
		shutil.rmtree(english_path)


def run_makemessages():
	"""Run makemessages command for english po files"""
	logging.info("Executing makemessages command")
	# Generate english po file
	ignore_pattern = ['python-packages/*']
	management.call_command('makemessages', locale='en', ignore_patterns=ignore_pattern, no_obsolete=True)
	# Generate english po file for javascript
	ignore_pattern = ['kalite/static/admin/js/*', 'python-packages/*']
	management.call_command('makemessages', domain='djangojs', locale='en', ignore_patterns=ignore_pattern, no_obsolete=True)


def update_templates():
	"""Update template po files"""
	logging.info("Posting template po files to static/pot/")
	## post them to exposed URL
	static_path = os.path.join(settings.STATIC_ROOT, "pot/")
	ensure_dir(static_path)
	shutil.copy(os.path.join(settings.LOCALE_PATHS[0], "en/LC_MESSAGES/django.po"), os.path.join(static_path, "kalite.pot"))
	shutil.copy(os.path.join(settings.LOCALE_PATHS[0], "en/LC_MESSAGES/djangojs.po"), os.path.join(static_path, "kalitejs.pot"))


def generate_test_files():
	"""Insert asterisks as translations in po files"""

	# Open them up and insert asterisks for all empty msgstrs
	logging.info("Generating test po files")
	en_po_dir = os.path.join(settings.LOCALE_PATHS[0], "en/LC_MESSAGES/")
	for po_file in os.listdir(en_po_dir):
		if not po_file.endswith(".po"):
			continue
		else:
			with open(os.path.join(en_po_dir, "tmp.po"), 'w') as temp_file:
				msgstr_pattern = re.compile(r'msgstr \"\"')
				empty_translation = re.compile(r'\"\"')
				variables_pattern = re.compile(r'%\(\w+\)[s,d]')
				new_msgstr = "msgstr \"*********\""
				lines = open(os.path.join(en_po_dir, po_file), 'r').readlines()
				counter = 0 
				variables = []
				for line in lines:
					if counter < 18: # the first 18 lines are descriptive and not part of the translations (this is a hack to skip the first empty msgstr without making a complicated regex)
						temp_file.write(line)
					else:
						variables += re.findall(variables_pattern, line)
						msgid_content = re.search('(?<=msgid ").+(?=")', line) or ""
						if msgid_content:
							new_msgstr = "msgstr \"*%s*\"" % msgid_content.group(0)
							
							# new_line = msgstr_pattern.sub("msgstr \"*****\"", line) #replaces line with asterisks
						
						new_line = msgstr_pattern.sub(new_msgstr, line)
 						# insert variables if necessary
 						# if new_line != line and variables:
 						# 	import pdb; pdb.set_trace()
							# variables_str = " ".join(variables)
							# new_line += variables_str
							# variables = [] # reset
						temp_file.write(new_line)
					counter += 1
				temp_file.close()

			# Once done replacing, rename temp file to overwrite original
			os.rename(os.path.join(en_po_dir, "tmp.po"), os.path.join(en_po_dir, po_file))
			
			compile_all_po_files()

def compile_all_po_files():
	"""Compile all po files in locale directory"""
	# before running compilemessages, ensure in correct directory
	move_to_project_root()
	(out, err, rc) = call_command_with_output('compilemessages')
	if err:
		logging.debug("Error executing compilemessages: %s" % err)
	return out, err, rc
