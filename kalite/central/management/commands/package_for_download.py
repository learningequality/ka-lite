"""
Placeholder for function that will wrap kalite in
"""
import json
import inspect
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


def install_from_package(install_json_file, signature_file, zip_file, dest_dir=None):
    import os
    import platform
    import shutil
    import sys
    from zipfile import ZipFile

    # Make the true paths
    src_dir = os.path.dirname(__file__)
    install_json_file = os.path.join(src_dir, install_json_file)
    signature_file = os.path.join(src_dir, signature_file)
    zip_file = os.path.join(src_dir, zip_file)

    # Validate the unpacked files
    for file in [install_json_file, signature_file, zip_file]:
        if not os.path.exists(file):
            raise Exception("Could not find expected file from zip package: %s" % file)

    # get the destination directory
    while not dest_dir or not os.path.exists(dest_dir):
        if dest_dir:
            sys.stderr.write("Path does not exist: %s" % dest_dir)
        dest_dir = raw_input("Please enter the directory where you'd like to install KA Lite (blank=%s): " % src_dir) or src_dir

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

    shutil.copy(install_json_file, os.path.join(dest_dir, "kalite/static/data/"))

    # Run the install/start scripts
    script_extension = ("bat" if platform.platform() == "Windows" else "sh")
    return_code = os.system(os.path.join(dest_dir, "install.%s" % script_extension))
    if return_code != 0:
        sys.stderr.write("Failed to install KA Lite.")
        sys.exit(return_code)
    return_code = os.system(os.path.join(dest_dir, "start.%s" % script_extension))
    if return_code != 0:
        sys.stderr.write("Failed to start KA Lite.")
        sys.exit(return_code)

    # move the data file to the expected location
    os.mkdir(os.path.join(dest_dir, "kalite/static/zip"))
    shutil.move(zip_file, os.path.join(dest_dir, "kalite/static/zip/"))
    shutil.move(signature_file, os.path.join(dest_dir, "kalite/static/zip/"))
    os.remove(install_json_file)  # was copied in earlier


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
    
    install_py_file = "install_from_zip.py"

    def handle(self, *args, **options):

        # Get the zone, remove so we can pass the rest of the options
        #   to the zip procedure
        zone_id = options["zone_id"]
        del options["zone_id"]
        wrapper_filename = options["file"] or os.path.join(tempfile.mkdtemp(), "package_" + create_default_archive_filename(options))

        def create_json_file():
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
            return models_file
        models_file = create_json_file()

        # Pre-zip prep #2:
        #   Create the install script.
        def create_install_files():
            install_files = {}

            install_files[self.install_py_file] = tempfile.mkstemp()[1]
            with open(install_files[self.install_py_file], "w") as fp:
                for srcline in inspect.getsourcelines(install_from_package)[0]:
                    fp.write(srcline)
                fp.write("\ninstall_from_package(\n")
                fp.write("    zip_file='%s',\n" % UpdateCommand.inner_zip_filename)
                fp.write("    signature_file='%s',\n" % UpdateCommand.signature_filename)
                fp.write("    install_json_file='%s',\n" % InitCommand.install_json_filename)
                fp.write(")\n")
                fp.write("print 'Installation completed!'")
            
            # Create clickable scripts: unix
            install_sh_file = self.install_py_file[:-3] + ".sh"
            install_files[install_sh_file] = tempfile.mkstemp()[1]
            with open(install_files[install_sh_file], "w") as fp:
                fp.write(open(os.path.realpath(settings.PROJECT_PATH + "/../python.sh"), "r").read())
                fp.write('current_dir=`dirname "${BASH_SOURCE[0]}"`')
                fp.write('\n$PYEXEC "$current_dir/%s"' % self.install_py_file)

            # Create clickable scripts: mac
            install_command_file = self.install_py_file[:-3] + ".command"
            install_files[install_command_file] = tempfile.mkstemp()[1]
            with open(install_files[install_command_file], "w") as fp:
                fp.write('current_dir=`dirname "${BASH_SOURCE[0]}"`')
                fp.write('\nsource "$current_dir/%s"' % install_sh_file)

            # Create clickable scripts: windows
            install_bat_file = self.install_py_file[:-3] + ".bat"
            install_files[install_bat_file] = tempfile.mkstemp()[1]
            with open(install_files[install_bat_file], "w") as fp:
                fp.write("start /b /wait python.exe %s" % self.install_py_file)

            # Change permissions
            for fil in install_files.values():
                os.chmod(fil, 0775)

            return install_files
        install_files = create_install_files()

        # Pre-zip prep #3:
        #   Generate the INNER zip
        def create_zip_file():
            zip_file = create_default_archive_filename(options)
            options["file"] = zip_file
            if settings.DEBUG or not os.path.exists(zip_file):  # always regenerate in debug mode
                call_command("zip_kalite", **options)
            if not os.path.exists(zip_file):
                raise CommandError("Failed to create kalite zip file.")
            return zip_file
        zip_file = create_zip_file()

        # Pre-zip prep #4:
        #   Create a file with the inner zip file signature.
        def create_signature_file(zip_file):
            signature_file = tempfile.mkstemp()[1]
            key = Device.get_own_device().get_key()
            signature = key.sign(crypto.encode_base64(open(zip_file, "rb").read()))
            with open(signature_file, "w") as fp:
                fp.write(signature)
            return signature_file
        signature_file = create_signature_file(zip_file)

        # Open the zip file for writing
        with ZipFile(wrapper_filename, "w", ZIP_STORED if settings.DEBUG else ZIP_DEFLATED) as zfile:
            # Dump the zip file
            zfile.write(zip_file,       arcname=UpdateCommand.inner_zip_filename)
            zfile.write(signature_file, arcname=UpdateCommand.signature_filename)
            zfile.write(models_file,    arcname=InitCommand.install_json_filename)
            for arcname, filename in install_files.iteritems():
                #zfile.write(install_file,   arcname="install.py")  # hard-coded because only the user uses it
                info = ZipInfo(arcname)
                info.external_attr = 0775 << 16L # give full access to included file
                with open(filename, "r") as fh:
                    zfile.writestr(info, fh.read())

        # cleanup
        os.remove(signature_file)
        os.remove(models_file)
        for fil in install_files.values():
            os.remove(fil)

        sys.stdout.write("Successfully packaged KA Lite to %s.\n" % wrapper_filename)
        
        
        # To test:
        #   Unpack to a temporary folder, then run install
        if options["auto_unpack"]:
            def simulate_enduser_experience():
                # unpack the inner zip to the destination
                dest_dir = tempfile.mkdtemp()
                sys.stdout.write("TEST: Unpacking and installing to %s\n" % dest_dir)

                # Simulate a user unpacking the zip
                zip = ZipFile(wrapper_filename, "r")
                for afile in zip.namelist():
                    zip.extract(afile, path=dest_dir)

                # Simulate the user running the script
                raise NotImplementedError()
            simulate_enduser_experience()