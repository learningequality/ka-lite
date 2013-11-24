"""
This command packages all parts together necessary for install and update.
  The package (zip) generally contains:
  * An inner zip file--the KA Lite source files
  * A signature file, containing the signature of the zip file with the central server's private key, validating the zip's contents.
  * a JSON file, containing models relevant to install (including the central server Device model, and any models relevant to the install)
  * A set of install scripts--a main python one, and clickable scripts per OS-type

This file also defines a function, "install_from_package", which extracts the 
  contents of the package and uses them, ultimately running install and 
  starting the server.  That function is extracted (using inspection)
  and written into the package, so that it stays tightly tied to this
  packaging logic, and so that it can be called both inline during testing,
  and externally after the package has been downloaded.
"""
import contextlib
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
import utils.platforms
from kalite.management.commands.zip_kalite import create_default_archive_filename, Command as ZipCommand
from securesync import engine
from securesync.management.commands.initdevice import Command as InitCommand
from securesync.models import Zone, DeviceZone, Device, ChainOfTrust, ZoneInvitation
from settings import LOG as logging
from utils.general import get_module_source_file
from utils.platforms import is_windows, system_script_extension, system_specific_zipping, system_specific_unzipping
from updates.management.commands.update import Command as UpdateCommand


def install_from_package(data_json_file, signature_file, zip_file, dest_dir=None, install_files=[]):
    """
    NOTE: This docstring (below this line) will be dumped as a README file.
    Congratulations on downloading KA Lite!  These instructions will help you install KA Lite.
    """
    import glob
    import os
    import shutil
    import sys

    # Make the true paths
    src_dir = os.path.dirname(__file__) or os.getcwd()  # necessary on Windows
    data_json_file = os.path.join(src_dir, data_json_file)
    signature_file = os.path.join(src_dir, signature_file)
    zip_file = os.path.join(src_dir, zip_file)

    # Validate the unpacked files
    for file in [data_json_file, signature_file, zip_file]:
        if not os.path.exists(file):
            raise Exception("Could not find expected file from zip package: %s" % file)

    # get the destination directory
    while not dest_dir or not os.path.exists(dest_dir) or raw_input("%s: Directory exists; install? [Y/n] " % dest_dir) not in ["", "y", "Y"]:
        if dest_dir and raw_input("%s: Directory does not exist; Create and install? [y/N] " % dest_dir) in ["y","Y"]:
            try:
                os.makedirs(os.path.realpath(dest_dir)) # can't use ensure_dir; external dependency.
                break
            except Exception as e:
                sys.stderr.write("Failed to create dest dir (%s): %s\n" % (dest_dir, e))
        dest_dir = raw_input("Please enter the directory where you'd like to install KA Lite (blank=%s): " % src_dir) or src_dir

    # unpack the inner zip to the destination
    system_specific_unzipping(zip_file, dest_dir)
    sys.stdout.write("\n")

    # Copy, so that if the installation fails, it can be restarted
    shutil.copy(data_json_file, os.path.join(dest_dir, "kalite/static/data/"))

    # Run the setup/start scripts
    files = [f for f in glob.glob(os.path.join(dest_dir, "setup*%s" % system_script_extension())) if not "from_zip" in f]
    return_code = os.system('"%s"' % files[0])
    if return_code:
        sys.stderr.write("Failed to set up KA Lite: exit-code = %s" % return_code)
        sys.exit(return_code)
    return_code = os.system('"%s"' % os.path.join(dest_dir, "start%s" % system_script_extension()))
    if return_code:
        sys.stderr.write("Failed to start KA Lite: exit-code = %s" % return_code)
        sys.exit(return_code)

    # move the data file to the expected location
    static_zip_dir = os.path.join(dest_dir, "kalite/static/zip")
    if not os.path.exists(static_zip_dir):
        os.mkdir(static_zip_dir)
    shutil.move(zip_file, static_zip_dir)
    shutil.move(signature_file, static_zip_dir)

    # Remove the remaining install files
    os.remove(data_json_file)  # was copied in earlier
    for f in install_files:
        fpath = os.path.join(src_dir, f)
        if not os.path.exists(fpath):
            continue
        try:
            os.remove(fpath)
            sys.stdout.write("Removed installation file %s\n" % fpath)
        except Exception as e:
            sys.stderr.write("Failed to delete installation file %s: %s\n" % (fpath, e))

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
        make_option('-i', '--include-data',
            action='store_true',
            dest='include_data',
            default=False,
            help='Include all data currently in a zone, into the installation json blob',
            metavar="INCLUDE_DATA"
        ),

        make_option('-a', '--auto-unpack',
            action='store',
            dest='auto_unpack',
            default=False,
            help='For test purposes, auto-unpack the zip file and install a server.',
            metavar="AUTO-UNPACK"
        ),
    )
    
    install_py_file = "install.py"

    def handle(self, *args, **options):

        # Get the zone, remove so we can pass the rest of the options
        #   to the zip procedure
        zone_id = options["zone_id"]
        del options["zone_id"]
        wrapper_filename = options["file"] or os.path.join(tempfile.mkdtemp(), "package_" + create_default_archive_filename(options))


        # Pre-zip prep #1:
        #   Create the json data file
        def create_json_file(include_data):
            central_server = Device.get_central_server()
            if not zone_id:
                models = [central_server] if central_server else []

            else:
                # Get a chain of trust to the zone owner.
                #   Because we're on the central server, this will
                #   simply be the central server, but in the future
                #   this would return an actual chain.
                logging.debug("Generating a zone invitation...")
                zone = Zone.objects.get(id=zone_id)
                chain = ChainOfTrust(zone=zone)
                assert chain.validate()
                new_invitation = ZoneInvitation.generate(zone=zone, invited_by=Device.get_own_device())
                new_invitation.save()  # keep a record of the invitation, for future revocation.  Also, signs the thing

                # This ordering of objects is a bit be hokey, but OK--invitation usually must be 
                #   inserted before devicezones--but because it's not pointing to any devices,
                #   it's OK to be at the end.
                # Note that the central server will always be at the front of the chain of trust,
                #   so no need to explicitly include.
                models = chain.objects() + [new_invitation]

                # 
                if include_data:
                    logging.debug("Serializing entire dataset...")
                    devices = Device.objects.by_zone(zone)
                    devicezones = DeviceZone.objects.filter(zone=zone)
                    models += list(devices) + list(devicezones)
                    models += engine.get_models(zone=zone, limit=None)  # get all models on this zone

            models_file = tempfile.mkstemp()[1]
            with open(models_file, "w") as fp:
                fp.write(engine.serialize(models))
            return models_file
        models_file = create_json_file(options["include_data"])

        # Pre-zip prep #2:
        #   Generate the INNER zip
        def create_inner_zip_file():
            zip_file = os.path.join(settings.MEDIA_ROOT, "zip", os.path.basename(create_default_archive_filename(options)))
            options["file"] = zip_file
            if settings.DEBUG or not os.path.exists(zip_file):  # always regenerate in debug mode
                call_command("zip_kalite", **options)
            if not os.path.exists(zip_file):
                raise CommandError("Failed to create kalite zip file.")
            return zip_file
        inner_zip_file = create_inner_zip_file()

        # Pre-zip prep #3:
        #   Create a file with the inner zip file signature.
        def create_signature_file(inner_zip_file):
            signature_file = os.path.splitext(inner_zip_file)[0] + "_signature.txt"
            logging.debug("Generating signature; saving to %s" % signature_file)
            if settings.DEBUG or not os.path.exists(signature_file):  # always regenerate in debug mode
                key = Device.get_own_device().get_key()
                chunk_size = int(2E5)  #200kb chunks
                signature = key.sign_large_file(inner_zip_file, chunk_size=chunk_size)
                with open(signature_file, "w") as fp:
                    fp.write("%d\n" % chunk_size)
                    fp.write(signature)
            return signature_file
        signature_file = create_signature_file(inner_zip_file)

        # Gather files together
        files_dict = {
            UpdateCommand.inner_zip_filename: inner_zip_file,
            UpdateCommand.signature_filename: signature_file,
            InitCommand.data_json_filename:   models_file,
        }

        # Pre-zip prep #4:
        #   Create the install scripts.
        def create_install_files(files_dict={}):
            install_files = {}  # need to keep track of, for later cleanup

            # Create clickable scripts: unix
            install_sh_file = self.install_py_file[:-3] + "_linux.sh"
            install_files[install_sh_file] = tempfile.mkstemp()[1]
            with open(install_files[install_sh_file], "w") as fp:
                fp.write("echo 'Searching for python path...'\n")
                fp.write(open(os.path.realpath(settings.PROJECT_PATH + "/../scripts/python.sh"), "r").read())
                fp.write('\ncurrent_dir=`dirname "${BASH_SOURCE[0]}"`')
                fp.write('\n$PYEXEC "$current_dir/%s"' % self.install_py_file)

            # Create clickable scripts: mac
            install_command_file = self.install_py_file[:-3] + "_mac.command"
            install_files[install_command_file] = tempfile.mkstemp()[1]
            with open(install_files[install_command_file], "w") as fp:
                fp.write('\ncurrent_dir=`dirname "${BASH_SOURCE[0]}"`')
                fp.write('\nsource "$current_dir/%s"' % install_sh_file)

            # Create clickable scripts: windows
            install_bat_file = self.install_py_file[:-3] + "_windows.bat"
            install_files[install_bat_file] = tempfile.mkstemp()[1]
            with open(install_files[install_bat_file], "w") as fp:
                fp.write("start /b /wait python.exe %s" % self.install_py_file)

            # Dump readme file
            readme_file = "README"
            install_files[readme_file] = tempfile.mkstemp()[1]
            with open(install_files[readme_file], "w") as fp:
                # First line of docstring is a message that the docstring will
                #   be the readme.  Remove that, dump the rest raw!
                fp.write(inspect.getdoc(install_from_package).split("\n", 2)[1])

            # NOTE: do this last, so we can pass the set of install files in the 
            #   function call, for effective cleanup.

            # Create the install python script,
            #   by outputting the install_from_package function (extracting here
            #   through inspection and dumping line-by-line), and its dependencies
            #   (utils.platforms, grabbed here through force).
            #
            # Also output a call to the function.
            install_files[self.install_py_file] = tempfile.mkstemp()[1]
            with open(install_files[self.install_py_file], "w") as fp:
                for srcline in inspect.getsourcelines(install_from_package)[0]:
                    fp.write(srcline)
                fp.write("\n%s\n" % open(get_module_source_file("utils.platforms"), "r").read())
                fp.write("\ninstall_from_package(\n")
                fp.write("    zip_file='%s',\n" % UpdateCommand.inner_zip_filename)
                fp.write("    signature_file='%s',\n" % UpdateCommand.signature_filename)
                fp.write("    data_json_file='%s',\n" % InitCommand.data_json_filename)
                fp.write("    install_files=%s,\n" % (files_dict.keys() + install_files.keys()))
                fp.write(")\n")
                fp.write("print 'Installation completed!'")

            return install_files
        install_files = create_install_files(files_dict=files_dict)

        # FINAL: Create the outer (wrapper) zip
        files_dict.update(install_files)
        system_specific_zipping(
            files_dict = files_dict,
            zip_file=wrapper_filename, 
            compression=ZIP_STORED if settings.DEBUG else ZIP_DEFLATED,
#            callback=None,
        )

        # cleanup
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