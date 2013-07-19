# Cron job to zip up most current srts into zipped_subs dir 
import os
import zipfile
import pdb
import sys

# HELP: Is there a better way to organize the below import of settings?
PROJECT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path = [PROJECT_PATH, os.path.join(PROJECT_PATH, "../../"), os.path.join(
	PROJECT_PATH, "../python-packages/")] + sys.path

import settings
import subtitle_utils

logger = subtitle_utils.setup_logging("zip_srt_files")

def generate_zipped_srts():
	# Create media directory if it doesn't yet exist
	media_root = settings.MEDIA_ROOT
	ensure_dir(media_root)
	zip_path = media_root + "subtitles/"
	ensure_dir(zip_path)
	locale_path = settings.LOCALE_PATHS[0]
	lang_dirs = os.listdir(locale_path)
	for lang_code in lang_dirs:
		if "subtitles" in os.listdir(locale_path + lang_code):
			zf = zipfile.ZipFile('%s%s_subtitles.zip' % (zip_path, lang_code), 'w')
			for root, dirs, files in os.walk("%s%s/subtitles/" % (locale_path, lang_code)):
				for f in files:
					zf.write(os.path.join(root, f), arcname=f)
			zf.close()
			logger.info("Zipped %s" % lang_code)


def ensure_dir(path):
	if not os.path.exists(path):
		os.makedirs(path)

if __name__ == '__main__':
	generate_zipped_srts()


