"""

The create_dummy_language_pack command downloads the 'en' language
pack from the central server and creates a new language pack based on
that. Make sure you have internet!

"""

import polib
import requests
import zipfile
from cStringIO import StringIO

from django.conf import settings
from django.core.management.base import NoArgsCommand

from kalite.i18n import get_language_pack_url

logging = settings.LOG

BASE_LANGUAGE_PACK = "en"       # language where we base the dummy langpack from


class Command(NoArgsCommand):

    def handle_noargs(self):
        langpack_zip = download_language_pack(lang)
        django_mo, djangojs_mo = retrieve_mo_file(langpack_zip)
        dummy_django_mo, dummy_djangojs_mo = (create_mofile_with_dummy_strings(django_mo),
                                              create_mofile_with_dummy_strings(djangojs_mo))
        # then save those dummy mos into po files
        # dummy_django_mo.save_as_pofile
        # dummy_djangojs_mo.save_as_pofile


def download_language_pack(lang):
    url = get_language_pack_url(lang)

    try:
        resp = requests.get(url)
        resp.raise_for_status()
    except requests.ConnectionError as e:
        logging.error("Error downloading %s language pack: %s" % (lang, e))

    return zipfile.ZipFile(StringIO(resp.content))


def retrieve_mo_files(langpack_obj):
    pass


def create_mofile_with_dummy_strings(mofile_obj):
    pass
