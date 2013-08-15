"""
This is for functions that help package KA Lite and deliver it to users.
"""
import os
import shutil
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED

import kalite
import settings
from utils.django_utils import call_command_with_output


def package_offline_install_zip(version=kalite.VERSION, platform="all", locale="all", server_type="local", zone=None, central_server="", force=False):
    """
    Does a bit of massaging to (efficiently, reusably) package the contents as requested, 
    and make the file requested available for download.
    """

    # Zone is there just for future compat. purposes.
    if zone:
        raise NotImplementedError()

    # assume server_type local for now, to shorten name.
    base_archive_name = "kalite-%s-%s-%s.zip" % (platform, locale, version) 
    base_archive_path = settings.STATIC_ROOT+ "/zip/" + base_archive_name

    # Make sure the correct base zip is created, based on platform and locale
    if force or not os.path.exists(base_archive_path):
        # Cannot request a past version that we don't have an existing archive for
        #    (or a future version, for that matter!)
        if version != kalite.VERSION:
            raise Exception("Version %s not available at this time." % version)

        if not os.path.exists(os.path.split(base_archive_path)[0]):
            os.mkdir(os.path.split(base_archive_path)[0])

        out = call_command_with_output("zip_kalite", version=version, platform=platform, locale=locale, server_type=server_type, central_server=central_server, file=base_archive_path)
        if out[1] or out[2]:
            raise Exception("Failed to create zip file(%d): %s" % (out[2], out[1]))

    # Append into the zip, on disk
    zip_file = tempfile.mkstemp()[1]
    shutil.copy(base_archive_path, zip_file) # duplicate the archive

    # Add local settings?
    
    # Slip in zone info
    return zip_file