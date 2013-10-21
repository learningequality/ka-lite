import json
import os
import requests
import zipfile
from optparse import make_option
from StringIO import StringIO

from django.core.management.base import BaseCommand, CommandError

import settings
import version
from settings import LOG as logging
from utils.general import ensure_dir
from main.models import LanguagePack


LOCALE_ROOT = settings.LOCALE_PATHS[0]

class Command(BaseCommand):
    help = "Download language pack requested from central server"

    option_list = BaseCommand.option_list + (
        make_option('-l', '--language',
                    action='store',
                    dest='lang_code',
                    default=None,
                    metavar="LANG_CODE",
                    help="Specify a particular language code to download language pack for."),
        make_option('-s', '--software_version',
                    action='store',
                    dest='software_version',
                    default=None,
                    metavar="SOFT_VERS",
                    help="Specify the software version to download a language pack for."),
    )

    def handle(self, *args, **options):
        code = options["lang_code"]
        software_version = options["software_version"]
        if not code:
            raise CommandError("You must specify a language to download a language pack for.")
        if not software_version:
            raise CommandError("You must specify a software version to download a language pack for.")

        ## Download the language pack
        zip_file = get_language_pack(code, software_version)

        ## Unpack into locale directory
        unpack_language(code, zip_file)

        ## Update database with meta info
        update_database(code)


def get_language_pack(code, software_version):
    """Download language pack for specified language"""

    logging.info("Retrieving language pack: %s" % code)
    request_url = "http://%s/static/language_packs/%s/%s.zip" % (settings.CENTRAL_SERVER_HOST, software_version, code)
    r = requests.get(request_url)
    try:
        r.raise_for_status()
    except Exception as e:
        raise CommandError(e)

    return r.content

def unpack_language(code, zip_file):
    """Unpack zipped language pack into locale directory"""

    logging.info("Unpacking new translations")
    ensure_dir(os.path.join(LOCALE_ROOT, code, "LC_MESSAGES"))
    
    ## Unpack into temp dir
    z = zipfile.ZipFile(StringIO(zip_file))
    z.extractall(os.path.join(LOCALE_ROOT, code))


def update_database(code):
    """Create/update LanguagePack table in database based on given languages metadata"""

    metadata = json.loads(open(os.path.join(LOCALE_ROOT, code, "%s_metadata.json" % code)).read())

    logging.info("Updating database for language pack: %s" % code)
        
    pack, created = LanguagePack.objects.get_or_create(code=code, name=metadata["name"])
    for key, value in metadata.items():
        setattr(pack, key, value)
    pack.save()

    logging.info("Successfully updated database.")









