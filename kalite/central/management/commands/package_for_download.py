"""
Placeholder for function that will wrap kalite in
"""
import json
import os
import sys
import tempfile
from optparse import make_option
from zipfile import ZipInfo, ZipFile, ZIP_DEFLATED, ZIP_STORED

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

import settings
from kalite.management.commands.zip_kalite import create_default_archive_filename, Command as ZipCommand
from securesync import crypto
from securesync.management.commands.initdevice import Command as InitCommand
from securesync.models import Zone, DeviceZone, Device
from shared import serializers



def install_kalite_from_package(src_dir=None, dest_dir=None):
    import os
    import shutil
    import sys

    if not src_dir:
        src_dir = os.getcwd()
    install_json_file = os.path.join(src_dir, Command.install_json_filename)
    signature_file = os.path.join(src_dir, Command.signature_filename)
    kalite_zip_file = os.path.join(src_dir, Command.kalite_zip_filename)

    # Validate the unpacked files
    for file in [install_json_file, signature_file, kalite_zip_file]:
        if not os.path.exists(file):
            raise Exception("Could not find expected file from zip package: %s" % file)

    # get the destination directory
    while not dest_dir and not os.path.exists(dest_dir):
        if dest_dir:
            sys.stderr.write("Path does not exist: %s" % dest_dir)
        dest_dir = raw_input("Please enter the directory where you'd like to install KA Lite (blank=%s): " % src_dir) or src_dir

    # ignore the signature; nothing we can do with it.
    os.remove(signature_file)

    # unpack the inner zip to the destination
    zip = ZipFile(kalite_zip_file, "r")
    nfiles = len(zip.namelist())
    for fi,afile in enumerate(zip.namelist()):
        if fi>0 and fi%round(nfiles/10)==0:
            pct_done = round(100.*(fi+1.)/nfiles)
            sys.stdout.write(" %d%%" % pct_done)

        zip.extract(afile, path=dest_dir)
        # If it's a unix script or manage.py, give permissions to execute
        if os.path.splitext(afile)[1] == ".sh":
            os.chmod(os.path.realpath(dest_dir + "/" + afile), 0755)
            sys.stdout.write("\tChanging perms on script %s\n" % os.path.realpath(dest_dir + "/" + afile))
    sys.stdout.write("\n")

    # move the data file to the expected location
    shutil.move(install_json_file, os.path.join(dest_dir, "kalite/static/data/"))

    # run the install
    os.system(os.path.join(dest_dir, "install.sh"))
    os.system(os.path.join(dest_dir, "start.sh 9000"))
    os.system("python " + os.path.join(dest_dir, "kalite/manage.py syncmodels"))


class Command(BaseCommand):
    """
    When we package KA Lite for download, we want to include:
    * signature for the zip file
    * necessary objects for using the zip (like central server device)
    * any relevant local_settings (like central server)
    """
    install_json_filename = os.path.basename(InitCommand.install_json_file)
    signature_filename = "zip_signature.txt"
    kalite_zip_filename = "kalite.zip"

    option_list = ZipCommand.option_list + (
        make_option('-z', '--zone',
            action='store',
            dest='zone',
            default=None,
            help='Zone information to include',
            metavar="ZONE"
        ),
    )

    def handle(self, *args, **options):

        # Get the zone, remove so we can pass the rest of the options
        #   to the zip procedure
        zone_id = options["zone"]
        del options["zone"]
        wrapper_filename = "package_" + create_default_archive_filename(options)

        # Generate the zip file
        zip_filename = options["file"] or create_default_archive_filename(options)
        if True or not os.path.exists(zip_filename):
            call_command("zip_kalite", **options)
        if not os.path.exists(zip_filename):
            raise CommandError("Failed to create kalite zip file.")

        # Open the zip file for writing
        with ZipFile(wrapper_filename, "w", ZIP_STORED) as zfile:
            # Dump the zip file
            zfile.write(zip_filename, self.kalite_zip_filename)

            # Create the json data file
            if zone_id:
                zone = Zone.objects.get(id=zone_id)
                models = zone.get_chain_of_trust()
            else:
                models = [Device.get_central_server()]
            fil = tempfile.mkstemp()[1]
            with open(fil, "w") as fp:
                fp.write(serializers.serialize("versioned-json", models))
            zfile.write(fil, arcname=self.install_json_filename)
            #os.remove(fil)

            # Sign the zip file and add to the archive
            fil = tempfile.mkstemp()[1]
            key = Device.get_own_device().get_key()
            signature = key.sign(crypto.encode_base64(open(zip_filename, "rb").read()))
            with open(fil, "w") as fp:
                fp.write(signature)
            zfile.write(fil, arcname=self.signature_filename)
            #os.remove(fil)

        sys.stdout.write("Successfully packaged KA Lite to %s.\n" % wrapper_filename)
        
        
        # To test:
        #   Unpack to a temporary folder, then run install
        if settings.DEBUG:
            # unpack the inner zip to the destination
            dest_dir = tempfile.mkdtemp()
            sys.stdout.write("TEST: Unpacking and installing to %s\n" % dest_dir)

            zip = ZipFile(wrapper_filename, "r")
            for afile in zip.namelist():
                zip.extract(afile, path=dest_dir)
            install_kalite_from_package(src_dir=dest_dir, dest_dir=dest_dir)