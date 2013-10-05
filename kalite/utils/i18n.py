"""
Utility functions for i18n related tasks on the distributed server
"""

import os
import json

import settings

class MetaDataNotFound(Exception):

    def __str__(value):
        return "Meta data JSON file not found"

def get_installed_languages():
	"""Return dictionary of currently installed languages and meta data"""

	installed_languages = []

	# Loop through locale folder
	locale_dir = settings.LOCALE_PATHS[0]

	for lang in os.listdir(locale_dir):
		# Inside each folder, read from the JSON file - language name, % UI trans, version number
		try:
			lang_meta = json.loads(open(os.path.join(locale_dir, lang, "%s_metadata.json" % lang)).read())
		except:
			raise MetaDataNotFound()
		lang = lang_meta
		installed_languages.append(lang)

	# return installed_languages
	return installed_languages