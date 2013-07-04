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


def package_offline_install_zip(platform, locale, server_type="local", zone=None, num_certificates=1, central_server=""):

    # assume server_type local for now, to shorten name.
    base_archive_name = "kalite-%s-%s-%s.zip" % (platform, locale, kalite.VERSION) 
    base_archive_path = settings.STATIC_ROOT+ "/zip/" + base_archive_name
    
    # This is just for demo purposes;
    #   in the future, certificates are only generated
    #   when the form is submitted.
    
    # Generate NEW certificates (into the db), as to keep enough for everybody
    if zone:
        certs = zone.generate_install_certificates(num_certificates=num_certificates)

        # Stream out the relevant offline install data
        from securesync.utils import dump_zone_for_offline_install
        models_json_file = tempfile.mkstemp()[1]
        dump_zone_for_offline_install(zone_id=zone.id, out_file=models_json_file, certs=certs)
        
    # Make sure the correct base zip is created, based on platform and locale
    if not os.path.exists(base_archive_path):
        if not os.path.exists(os.path.split(base_archive_path)[0]):
            os.mkdir(os.path.split(base_archive_path)[0])

        out = call_command_with_output("zip_kalite", platform=platform, locale=locale, server_type=server_type, central_server=central_server, file=base_archive_path)
        if out[1] or out[2]:
            raise Exception("Failed to create zip file(%d): %s" % (out[2], out[1]))
                            
    # Append into the zip, on disk
    # TODO(bcipolli) the zip_file should be a read/writable self-disappearing temp file;
    #  not via mkstemp()
    zip_file = tempfile.mkstemp()[1]
    shutil.copy(base_archive_path, zip_file) # duplicate the archive
    if settings.DEBUG: # avoid "caching" "problem" in DEBUG mode
        try: os.remove(base_archive_path)# clean up
        except: pass

    with ZipFile(zip_file, "a", ZIP_DEFLATED) as zh:
        if zone:
            zh.write(models_json_file, arcname="kalite/static/data/zone_data.json")
            try: os.remove(models_json_file)# clean up
            except: pass
    
    return zip_file