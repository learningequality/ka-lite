import logging
import os
import shutil
import platform
import tempfile
from optparse import make_option
from zipfile import ZipInfo, ZipFile, ZIP_DEFLATED, ZIP_STORED

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

import settings
import version


## The following 3 functions define the rules for inclusion/exclusion

def file_in_platform(file_path, platform):
    """Logic on whether to include or exclude a file,
    based on the requested platform and the file's name (including path)"""

    ext = os.path.splitext(file_path)[1]

    if platform == "all":
        return True

    elif platform == "windows":  # remove non-windows files
        return ext not in [".sh",]

    else:  # remove windows files
        return ext not in [".vbs", ".bat"]


def select_package_dirs(dirnames, key_base, **kwargs):
    """Choose which directories to include/exclude,
    based on the "key-base", which is essentially the relative path from the ka-lite project"""
    base_name = os.path.split(key_base)[1]

    if key_base == "":  # base directory
        in_dirs = set(('docs', 'kalite', 'locale', 'python-packages'))

    elif base_name in ["locale", "localflavor"] and kwargs.get("locale", ""):
        # ONLY include files for the particular locale

        in_dirs = set((kwargs['locale'],))

    else:
        # can't exclude 'test', which eliminates the Django test client (used in caching)
        #   as well as all the Khan academy tests
        in_dirs = set(dirnames)
        if kwargs["remove_test"]:
            in_dirs -= set(('loadtesting', 'tests', 'testing', 'tmp', 'selenium', 'werkzeug', 'postmark'))
        #
        if kwargs.get("server_type", "") != "central":
            in_dirs -= set(("central", "landing-page"))
            if base_name in ["kalite", "templates"]:  # remove central server apps & templates
                in_dirs -= set(("contact", "faq", "registration"))

    return in_dirs


def file_in_blacklist_set(file_path):
    """Generic filter to eliminate particular filenames and extensions.

    Note: explicitly keep out local_settings"""

    name = os.path.split(file_path)[1]
    ext = os.path.splitext(file_path)[1]
    return (ext in [".pyc",".sqlite",".zip",'.xlsx',]) or (name in ["local_settings.py", ".gitignore", "tests.py", "faq",".DS_Store"])


# Filter-less functions (just logic)

def recursively_add_files(dirpath, files_dict=dict(), key_base="", **kwargs):
    """Recurses into the directories of dirpath to add files to files_dict.

    files_dict: key is source path, value is a dict including dest_path (in archive)
    key_base:the relative path from the ka-lite project; used to identify
             the location in the project when including/excluding files/dirs
    """

    for (root, dirnames, filenames) in os.walk(dirpath):

        #
        in_dirs = select_package_dirs(dirnames, key_base=key_base, **kwargs)

        # Base case: loop all files in this directory
        for f in filenames:
            file_path = os.path.join(dirpath, f)

            if file_in_blacklist_set(file_path=file_path):
                continue
            elif not file_in_platform(file_path=file_path, platform=kwargs.get("platform", "all")):
                continue

            # Made it through!  Include in the package
            files_dict[file_path] = {
                "dest_path": os.path.join(key_base, f)
            }

        # Recursive case: loop all subdirectories
        for d in in_dirs:
            files_dict = recursively_add_files(
                dirpath = os.path.join(dirpath, d),
                files_dict = files_dict,
                key_base = os.path.join(key_base, d),
                **kwargs
            )

        break        # lazy to use walk; just break

    return files_dict


def create_local_settings_file(location, server_type="local", locale=None):
    """Create an appropriate local_settings file for the installable server."""

    fil = tempfile.mkstemp()[1]

    if settings.CENTRAL_SERVER:
        ls = open(fil, "w") # just in case fil is not unique, somehow...

    # duplicate local_settings when packaging from a local server
    elif os.path.exists(location):
        shutil.copy(location, fil)

    ls = open(fil, "a") #append, to keep those settings, but override SOME

    ls.write("\n") # never trust the previous file ended with a newline!
    ls.write("CENTRAL_SERVER = %s\n" % (server_type=="central"))
    if locale:
        ls.write("LANGUAGE_CODE = '%s'\n" % locale)
    ls.close()

    return fil


def create_default_archive_filename(options=dict()):
    """Generate a filename for the archive"""
    out_file = "kalite"
    out_file += "-%s" % options['platform']    if options['platform']    else ""
    out_file += "-%s" % options['locale']      if options['locale']      else ""
    out_file += "-%s" % options['server_type'] if options['server_type'] else ""
    out_file += "-v%s.zip" % version.VERSION

    return out_file


class Command(BaseCommand):
    help = "Create a zip file with all code, that can be unpacked anywhere."

    option_list = BaseCommand.option_list + (
        # Basic options
        make_option('-p', '--platform',
            action='store',
            dest='platform',
            default=platform.system(),
            help='OS PLATFORM to package for',
            metavar="PLATFORM"),
        make_option('-l', '--locale',
            action='store',
            dest='locale',
            default=None,
            help='LOCALE to package for',
            metavar="LOCALE"),
        make_option('-t', '--server-type',
            action='store',
            dest='server_type',
            default="local",
            help='KA Lite server type'),

        # Functional options
        make_option('-r', '--remove-test',
            action='store_true',
            dest='remove_test',
            default=False,
            help='Remove testing information?'),
        make_option('-n', '--nocompress',
            action='store_false',
            dest='compress',
            default=True,
            help='Avoid compressing'),
        make_option('-f', '--file',
            action='store',
            dest='file',
            default="__default__",
            help='FILE to save zip to',
            metavar="FILE"),
        )

    def handle(self, *args, **options):
        options['platform'] = options['platform'].lower() # normalize

        if options['platform'] not in ["all", "linux", "macos", "darwin", "windows"]:
            raise CommandError("Unrecognized platform: %s; will include ALL files." % options['platform'])

        # Step 1: recursively add all static files
        kalite_base = os.path.realpath(settings.PROJECT_PATH + "/../")
        files_dict = recursively_add_files(dirpath=kalite_base, **options)

        # Step 2: Add a local_settings.py file.
        #   For distributed servers, this is a copy of the local local_settings.py,
        #   with a few properties (specified as command-line options) overridden
        ls_file = create_local_settings_file(location=os.path.realpath(kalite_base+"/kalite/local_settings.py"), server_type=options['server_type'], locale=options['locale'])
        files_dict[ls_file] = { "dest_path": "kalite/local_settings.py" }

        # Step 3: select output file.
        if options['file']=="__default__":
            options['file'] = create_default_archive_filename(options)

        # Step 4: package into a zip file
        with ZipFile(options['file'], "w", ZIP_DEFLATED if options['compress'] else ZIP_STORED) as zfile:
            for srcpath,fdict in files_dict.items():
                if options['verbosity'] >= 1:
                    print "Adding to zip: %s" % srcpath
                # Add without setting exec perms
                if os.path.splitext(fdict["dest_path"])[1] != ".sh":
                    zfile.write(srcpath, arcname=fdict["dest_path"])
                # Add with exec perms
                else:
                    info = ZipInfo(fdict["dest_path"])
                    info.external_attr = 0755 << 16L # give full access to included file
                    with open(srcpath, "r") as fh:
                        zfile.writestr(info, fh.read())

