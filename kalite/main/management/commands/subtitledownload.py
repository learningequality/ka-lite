import requests
import sys 
import time
import urllib2
import zipfile


from django.core.management.base import BaseCommand, CommandError

from config.models import Settings
from updates.models import UpdateProcessLog

PROJECT_PATH = os.path.dirname(os.path.realpath(__file__)) + "/../"

sys.path = [PROJECT_PATH] + sys.path

import settings
from settings import LOG as logging

class Command(BaseCommand):
    help = "Download zip of subtitles of the indicated language"

    def handle(self, *args, **options):
        logging.info("Inside subtitle_download")
        language = Settings.get("subtitle_language")
            
        #  Create database entry 
        subtitle_download = UpdateProcessLog(process_name="subtitle download", stage_name="downloading")
        subtitle_download.save()

        # Download zip and update database with progress
        central_url = settings.CENTRAL_SERVER_DOMAIN
        f, file_path = tempfile.mkstemp()
        # file_path = "%s_subtitles.zip" % language

        response = urllib2.urlopen(central_url)
        # f = open(file_path, 'wb')
        meta = response.info()
        file_size = int(meta.getheaders("Content-Length")[0])

        file_size_dl = 0
        block_size = 8192
        while True:
            buffer = response.read(block_size)
            if not buffer:
                break

            file_size_dl += len(buffer)
            f.write(buffer)
            # Update database
            subtitle_download.stage_percent = float(file_size_dl/file_size)
            subtitle_download.save()
        f.close()

        # Once complete, save and move to next stage
        subtitle_download.stage_percent = 0
        subtitle_download.stage_name = "unpacking"
        subtitle_download.process_percent = 0.33
        subtitle_download.save()

        # Unpack it into content directory
        content_path = settings.CONTENT_ROOT
        with zipfile.ZipFile(file_path, 'r') as f:
            f.extractall(content_path)

        # Once complete, save and move to next stage
        subtitle_download.stage_name = "updating db"
        subtitle_download.process_percent = 0.66
        subtitle_download.save()
           
