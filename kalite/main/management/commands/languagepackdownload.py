import json
import os
import requests
import zipfile
from optparse import make_option
from StringIO import StringIO

from django.core.management.base import BaseCommand, CommandError

import settings
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
    )

    def handle(self, *args, **options):
        code = options.get("lang_code")
        if not code:
            raise CommandError("You must specify a language to download a language pack for.")

        ## Download the language pack
        zip_file = get_language_pack(code)

        ## Unpack into locale directory
        unpack_language(code, zip_file)

        ## Update database with meta info
        update_database(code)


def get_language_pack(code):
    """Download language pack for specified language"""

    logging.info("Retrieving language pack: %s" % code)
    request_url = "http://%s/static/language_packs/%s.zip" % (settings.CENTRAL_SERVER_HOST, code)
    r = requests.get(request_url)
    try:
        r.raise_for_status()
    except Exception as e:
        logging.error(e)

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

    import pdb; pdb.set_trace()
    try:
        metadata = json.loads(open(os.path.join(LOCALE_ROOT, code, "%s_metadata.json" % code)).read())
    except Exception as e:
        logging.error(e)

    logging.info("Updating database for language pack: %s" % code)
    try:
        pack, created = LanguagePack.objects.get_or_create(code=code, name=metadata.get("name"))
        pack.phrases = metadata.get("phrases")
        pack.approved_translations = metadata.get("translations_approved")
        pack.percent_translated = metadata.get("percent_approved_translations")
        pack.version = metadata.get("version")

        pack.save()
    except Exception as e:
        logging.error(e)
    else:
        logging.info("Successfully updated database.")









