"""A simple command to migrate any srt files in the static dir to the locale dir. Should only ever be run once."""

import glob
import os
import shutil

from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

import settings
from utils.general import ensure_dir


class Command(BaseCommand):
	help = 'Migrate any srt files in the static dir to the locale dir.'

	def handle(self, **options):
		"""Move srt files from static/srt to locale directory and file them by language code"""

		srt_root = os.path.join(settings.STATIC_ROOT, "srt")
		locale_root = settings.LOCALE_PATHS[0]

		for lang in os.listdir(srt_root):
			# Skips if not a directory
			if not os.path.isdir(os.path.join(srt_root, lang)):
				continue
			lang_srt_path = os.path.join(srt_root, lang, "subtitles/")
			lang_locale_path = os.path.join(locale_root, lang)
			ensure_dir(lang_locale_path)
			dst = os.path.join(lang_locale_path, "subtitles")

			for srt_file_path in glob.glob(os.path.join(lang_srt_path, "*.srt")):
				base_path, srt_filename = os.path.split(srt_file_path)
				if not os.path.exists(os.path.join(dst, srt_filename)):
					ensure_dir(dst)
					shutil.move(srt_file_path, os.path.join(dst, srt_filename))

		shutil.rmtree(srt_root)