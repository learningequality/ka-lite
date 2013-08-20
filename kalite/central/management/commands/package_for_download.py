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
from kalite.management.commands.update import Command as UpdateCommand
from securesync.management.commands.initdevice import Command as InitCommand
from securesync.models import Zone, DeviceZone, Device, ChainOfTrust, ZoneInvitation
from shared import serializers
from utils import crypto


def install_from_package(src_dir=None, dest_dir=None):
    import os
    import shutil
    import sys

    if not src_dir:
        src_dir = os.getcwd()
    install_json_file = os.path.join(src_dir, InitCommand.install_json_filename)
    signature_file = os.path.join(src_dir, UpdateCommand.signature_filename)
    zip_file = os.path.join(src_dir, UpdateCommand.inner_zip_filename)

    # Validate the unpacked files
    for file in [install_json_file, signature_file, zip_file]:
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
    zip = ZipFile(zip_file, "r")
    nfiles = len(zip.namelist())
    for fi,afile in enumerate(zip.namelist()):
        if fi>0 and fi%round(nfiles/10)==0:
            pct_done = round(100.*(fi+1.)/nfiles)
            sys.stdout.write(" %d%%" % pct_done)

        zip.extract(afile, path=dest_dir)
        # If it's a unix script or manage.py, give permissions to execute
        if os.path.splitext(afile)[1] == ".sh" or afile.endswith("manage.py"):
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

    option_list = ZipCommand.option_list + (
        make_option('-z', '--zone',
            action='store',
            dest='zone_id',
            default=None,
            help='Zone information to include',
            metavar="ZONE"
        ),
        make_option('-a', '--auto-unpack',
            action='store',
            dest='auto_unpack',
            default=False,
            help='For test purposes, auto-unpack the zip file and install a server.',
            metavar="AUTO-UNPACK"
        ),
    )

    def handle(self, *args, **options):

        # Get the zone, remove so we can pass the rest of the options
        #   to the zip procedure
        zone_id = options["zone_id"]
        del options["zone_id"]
        wrapper_filename = options["file"] or os.path.join(tempfile.mkdtemp(), "package_" + create_default_archive_filename(options))

        # Pre-zip prep #1:
        #   Create the json data file
        central_server = Device.get_central_server()
        if not zone_id:
            models = [central_server] if central_server else []
        else:
            zone = Zone.objects.get(id=zone_id)
            chain = ChainOfTrust(zone=zone)
            assert chain.validate()
            new_invitation = ZoneInvitation.generate(zone=zone, invited_by=Device.get_own_device())
            new_invitation.save()  # keep a record of the invitation, for future revocation.  Also, signs the thing
            models = [central_server] + chain.objects() + [new_invitation]

        models_file = tempfile.mkstemp()[1]
        with open(models_file, "w") as fp:
            fp.write(serializers.serialize("versioned-json", models))

        # Pre-zip prep #2:
        #   Generate the INNER zip file
        zip_filename = create_default_archive_filename(options)
        options["file"] = zip_filename
        if settings.DEBUG or not os.path.exists(zip_filename):  # always regenerate in debug mode
            call_command("zip_kalite", **options)
        if not os.path.exists(zip_filename):
            raise CommandError("Failed to create kalite zip file.")

        # Pre-zip prep #3:
        #   Create a file with the inner zip file signature.
        signature_file = tempfile.mkstemp()[1]
        key = Device.get_own_device().get_key()
        signature = key.sign(crypto.encode_base64(open(zip_filename, "rb").read()))
        with open(signature_file, "w") as fp:
            fp.write(signature)

        # Open the zip file for writing
        with ZipFile(wrapper_filename, "w", ZIP_STORED) as zfile:
            # Dump the zip file
            zfile.write(zip_filename, UpdateCommand.inner_zip_filename)

            zfile.write(models_file, arcname=InitCommand.install_json_filename)
            os.remove(models_file)

            # Sign the zip file and add to the archive
            zfile.write(signature_file, arcname=UpdateCommand.signature_filename)
            os.remove(signature_file)

        sys.stdout.write("Successfully packaged KA Lite to %s.\n" % wrapper_filename)
        
        
        # To test:
        #   Unpack to a temporary folder, then run install
        if options["auto_unpack"]:
            # unpack the inner zip to the destination
            dest_dir = tempfile.mkdtemp()
            sys.stdout.write("TEST: Unpacking and installing to %s\n" % dest_dir)

            zip = ZipFile(wrapper_filename, "r")
            for afile in zip.namelist():
                zip.extract(afile, path=dest_dir)
            install_from_package(src_dir=dest_dir, dest_dir=dest_dir)