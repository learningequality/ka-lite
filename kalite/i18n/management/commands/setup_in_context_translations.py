import StringIO
import os
import zipfile

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.core.management.base import NoArgsCommand
from fle_utils.general import ensure_dir

from kalite.version import SHORTVERSION


CROWDIN_URL_TEMPLATE = "https://api.crowdin.com/api/project/{project_identifier}/download/{lang}.zip?key={project_key}"
PSEUDOLANGUAGE = "en-US"


class Command(NoArgsCommand):

    def handle_noargs(self, **kwargs):

        if not settings.IN_CONTEXT_LOCALIZED:
            msg = "You must have settings.IN_CONTEXT_LOCALIZED = True if you want to run this command."
            raise ImproperlyConfigured(msg)

        project_id = os.environ.get("CROWDIN_PROJECT_ID")
        project_key = os.environ.get("CROWDIN_PROJECT_KEY")

        if not project_id or not project_key:
            msg = "You must have environment variables CROWDIN_PROJECT_ID and CROWDIN_PROJECT_KEY defined"
            raise ImproperlyConfigured(msg)

        url = CROWDIN_URL_TEMPLATE.format(
            project_identifier=project_id,
            project_key=project_key,
            lang=PSEUDOLANGUAGE,
        )

        resp = requests.get(url)
        resp.raise_for_status()

        f = StringIO.StringIO(resp.content)

        zf = zipfile.ZipFile(f, "r")

        zf_po_file_name = "versioned/{version}-django.po".format(version=SHORTVERSION)
        zf_js_po_file_name = "versioned/{version}-djangojs.po".format(version=SHORTVERSION)

        po_file_dir = os.path.join(settings.USER_WRITABLE_LOCALE_DIR, "en", "LC_MESSAGES")
        ensure_dir(po_file_dir)

        zf_po_file = zf.read(zf_po_file_name)
        zf_js_po_file = zf.read(zf_js_po_file_name)

        with open(os.path.join(po_file_dir, "django.po"), "w") as f:
            f.write(zf_po_file)

        with open(os.path.join(po_file_dir, "djangojs.po"), "w") as f:
            f.write(zf_js_po_file)

        call_command("compilemessages")
