"""
1. Download latest translations from CrowdIn
2. Store meta data incl: percent translated, version number, language
3. Compile po to mo
4. Zip everything up at exposed URL 
"""

import glob
import json
import os
import re
import requests
import shutil
import zipfile
import StringIO

from optparse import make_option
from django.core import management
from django.core.management.base import BaseCommand, CommandError

import settings
from utils.general import ensure_dir
from central.management.commands.cache_subtitles import get_language_name
from update_po import compile_all_po_files
from utils.general import ensure_dir

LOCALE_ROOT = settings.LOCALE_PATHS[0]
LANGUAGE_PACK_AVAILABILITY_FILENAME = "language_pack_availability.json"

class Command(BaseCommand):
	help = 'Caches latest translations from CrowdIn'

	def handle(self, **options):
		cache_translations()


def cache_translations():
	## Download from CrowdIn
	download_latest_translations() # this fcn will be broken until we get set up on CrowdIn, hopefully by next week

	## Loop through them, create/update meta data
	# generate_metadata()
	
	## Compile
	# compile_all_po_files()
	
	## Zip
	# zip_language_packs()


def download_latest_translations(project_id=settings.CROWDIN_PROJECT_ID, project_key=settings.CROWDIN_PROJECT_KEY, language_code="all"):
	"""Download latest translations from CrowdIn to corresponding locale directory."""
	# Note this won't download anything that we haven't manually created a folder for. 
	# CrowdIn API docs on downloading translations: http://crowdin.net/page/api/download
	# CrowdIn API docs for exporting entire project to zip archive: http://crowdin.net/page/api/export

	## Build latest package
	build_translations()

	## Get zip file of translations
	request_url = "http://api.crowdin.net/api/project/%s/download/%s.zip?key=%s" % (project_id, language_code, project_key)
	r = requests.get(request_url)
	r.raise_for_status()
	
	## Unpack into temp dir
	z = zipfile.ZipFile(StringIO.StringIO(r.content))
	tmp_dir_path = os.path.join(LOCALE_ROOT, "tmp")
	z.extractall(tmp_dir_path)

	## Copy over new translations
	extract_new_po(tmp_dir_path)

	# Clean up tracks
	if os.path.exists(tmp_dir_path):
		shutil.rmtree(tmp_dir_path)


def build_translations(project_id=settings.CROWDIN_PROJECT_ID, project_key=settings.CROWDIN_PROJECT_KEY):
	"""Build latest translations into zip archive on CrowdIn"""

	request_url = "http://api.crowdin.net/api/project/%s/export?key=%s" % (project_id, project_key)
	r = requests.get(request_url)
	r.raise_for_status()


def extract_new_po(tmp_dir_path=os.path.join(LOCALE_ROOT, "tmp")):
	"""Move newly downloaded po files to correct location in locale direction"""

	for lang in os.listdir(tmp_dir_path):
		# ensure directory exists in locale folder, and then overwrite local po files with new ones 
		ensure_dir(os.path.join(LOCALE_ROOT, lang, "LC_MESSAGES"))
		for po_file in glob.glob(os.path.join(tmp_dir_path, lang, "*/*.po")): 
			if "js" in os.path.basename(po_file):
				shutil.copy(po_file, os.path.join(LOCALE_ROOT, lang, "LC_MESSAGES", "djangojs.po"))
			else:
				shutil.copy(po_file, os.path.join(LOCALE_ROOT, lang, "LC_MESSAGES", "django.po"))


def generate_metadata():
	"""Loop through locale folder, create or update language specific meta and create or update master file."""
	# Open master file 
	try: 
		master_file = json.loads(open(os.path.join(LOCALE_ROOT, LANGUAGE_PACK_AVAILABILITY_FILENAME)).read())
	except:
		master_file = []

	# loop through all languages in locale, generate and write metadata, update master file
	for lang in glob.glob('%s*/' % LOCALE_ROOT):
		percent_translated = calculate_percent_translated(os.path.join(LOCALE_ROOT, lang, "LC_MESSAGES"))
		lang_metadata = {
			"code": lang,
			"name": get_language_name(lang),
			"percent_translated": percent_translated,
			"version": increment_version(lang, percent_translated, os.path.join(LOCALE_ROOT, lang))
		}
		# Write local TODO(Dylan): probably don't need to write this local version - seems like a duplication of effort
		with open(os.path.join(LOCALE_ROOT, lang, "%s_metadata.json" % lang), 'w') as output:
			json.dump(lang_metadata, output)
		
		# Update master
		master_file.append(lang_metadata)

	# Save updated master
	with open(os.path.join(settings.LANGUAGE_PACK_ROOT, LANGUAGE_PACK_AVAILABILITY_FILENAME), 'w') as output:
		json.dump(master_file, output) 


def calculate_percent_translated(po_file_path):
	"""Return total percent translated of entire language"""
	# add up totals for each file
	total_strings, total_translated = 0, 0
	for po_file in glob.glob('%s/*.po' % po_file_path):
		# Read it, count up filled msgids and filled msgstrs
		po_as_string = open(os.path.join(po_file_path, po_file)).read()
		total_strings += len(re.findall(r'msgid \".+\"', po_as_string))
		total_translated += len(re.findall(r'msgstr \".+\"', po_as_string))

	# Calc percent
	percent_trans = round(float(total_translated)/float(total_strings), 3) # without floats, too inexact
	return percent_trans


def increment_version(lang_code, percent_translated, lang_locale_path):
	"""Increment language pack version if translations have been updated"""
	#TODO(Dylan): this actually isn't that good of a way of knowing if things changed.. could be tricked easily.
	try:
		old_metadata = json.loads(open(os.path.join(lang_locale_path, "%s_metadata.json" % lang_code)).read())
	except:
		version = 1
	else:
		old_version = old_metadata.get("version")
		if old_metadata.get("percent_translated") != percent_translated:
			version = old_version + 1
		else: 
			version = old_version
	return version



def zip_language_packs():
	"""Zip up and expose all language packs"""
	ensure_dir(settings.LANGUAGE_PACK_ROOT)
	for lang in os.listdir(LOCALE_ROOT):
		# Create a zipfile for this language
		z = zipfile.ZipFile(os.path.join(settings.LANGUAGE_PACK_ROOT, "%s_lang_pack.zip" % lang), 'w')
		# Get every single file in the directory and zip it up
		lang_locale_path = os.path.join(LOCALE_ROOT, lang)
		for metadata_file in glob.glob('%s/*.json' % lang_locale_path):
			z.write(os.path.join(lang_locale_path, metadata_file), arcname=os.path.basename(metadata_file))	
		for po_file in glob.glob('%s/LC_MESSAGES/*.po' % lang_locale_path):
			z.write(os.path.join(lang_locale_path, po_file), arcname=os.path.join("LC_MESSAGES", os.path.basename(po_file)))	
		z.close()





