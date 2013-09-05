"""
System = Windows, Linux, etc
Platform = WindowsXP-SP3, etc.

This file is for functions that take system- and platform-specific 
information, and try to make them accessible generically (at least for our purposes).
"""
import os
import platform
import sys
import tempfile
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED, is_zipfile


def is_windows(system=None):
    """Right? :)"""
    system = system or platform.system()
    return system.lower() == "windows"


def is_osx(system=None):
    system = system or platform.system()
    return system.lower() == "darwin"


def system_script_extension():
    """
    System script extension (duh)
    """
    return ".bat" if is_windows() else ".sh"

def system_specific_scripts(system=None):
    """
    Set of all script files specific to a system
    """
    if is_windows(system):
        return [".bat", ".vbs"]
    else:
        return [".sh"]

def not_system_specific_scripts(system=None):
    if is_windows(system):
        return system_specific_scripts("linux")
    else:
        return system_specific_scripts("windows")


def _default_callback_zip(src_path, fi, nfiles):
    sys.stdout.write("Adding to zip (%d of %d): %s\n" % (fi + 1, nfiles, src_path))

def system_specific_zipping(files_dict, zip_file=None, compression=ZIP_DEFLATED, callback=_default_callback_zip):
    # Step 4: package into a zip file

    if not zip_file:
        zip_file = tempfile.mkstemp()[1]
    with ZipFile(zip_file, "w", compression) as zfile:
        for fi, (src_path, dest_path) in enumerate(files_dict.iteritems()):
            if callback:
                callback(src_path, fi, len(files_dict))
            # Add without setting exec perms
            if os.path.splitext(dest_path)[1] not in system_specific_scripts(system="linux"):
                zfile.write(src_path, arcname=dest_path)
            # Add with exec perms
            else:
                info = ZipInfo(dest_path)
                info.external_attr = 0755 << 16L # give full access to included file
                with open(src_path, "r") as fh:
                    zfile.writestr(info, fh.read())


def _default_callback_unzip(afile, fi, nfiles):
    """
    Private (default) callback function for system_specific_unzipping
    """
    if fi>0 and fi%round(nfiles/10)==0:
        pct_done = round(100. * (fi + 1.) / nfiles)
        sys.stdout.write(" %d%%" % pct_done)
        sys.stdout.flush()

    if (not is_windows()) and (os.path.splitext(afile)[1] in system_specific_scripts() or afile.endswith("manage.py")):
        sys.stdout.write("\tChanging perms on script %s\n" % afile)

def system_specific_unzipping(zip_file, dest_dir, callback=_default_callback_unzip):
    """
    # unpack the inner zip to the destination
    """

    if not os.path.exists(dest_dir):
        os.mkdir(dest_dir)

    if not is_zipfile(zip_file):
        raise Exception("bad zip file")

    zip = ZipFile(zip_file, "r")
    nfiles = len(zip.namelist())

    for fi, afile in enumerate(zip.namelist()):
        if callback:
            callback(afile, fi, nfiles)

        zip.extract(afile, path=dest_dir)
        # If it's a unix script or manage.py, give permissions to execute
        if (not is_windows()) and (os.path.splitext(afile)[1] in system_specific_scripts() or afile.endswith("manage.py")):
            os.chmod(os.path.realpath(dest_dir + "/" + afile), 0755)
