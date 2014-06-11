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
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED, is_zipfile, BadZipfile

ALL_SYSTEMS = ["windows", "darwin", "linux"]


def get_os_name():
    try:
        return ", ".join(platform.uname() + ("Python %s" % platform.python_version(),))
    except:
        try:
            return sys.platform
        except:
            return ""


def is_windows(system=None):
    system = system or platform.system()
    return system.lower() == "windows"


def is_osx(system=None):
    system = system or platform.system()
    return system.lower() in ["darwin", "macosx"]


def system_script_extension(system=None):
    """
    The extension for the one script that could be considered "the os script" for the given system..
    """
    exts = {
        "windows": ".bat",
        "darwin": ".command",
        "linux": ".sh",
    }
    system = system or platform.system()
    return exts.get(system.lower(), ".sh")


def system_specific_scripts(system=None):
    """
    All scripting types for that platform, that wouldn't be recognized
    on ALL other platforms.
    """
    if is_windows(system):
        return [".bat", ".vbs"]
    elif is_osx(system):
        return [".command", ".sh"]
    else:
        return [".sh"]

def not_system_specific_scripts(system=None):
    """
    Returns a list of all platform-specific scripts
    that are on OTHER systems and not on this one.
    (useful for removing unnecessary files from lists)
    """
    all_scripts = [fil for syst in ALL_SYSTEMS for fil in system_specific_scripts(syst)]
    return list(set(all_scripts) - set(system_specific_scripts(system)))


def _default_callback_zip(src_path, fi, nfiles):
    """Default callback function for system_specific_zipping"""
    sys.stdout.write("Adding to zip (%d of %d): %s\n" % (fi + 1, nfiles, src_path))


def system_specific_zipping(files_dict, zip_file=None, compression=ZIP_DEFLATED, callback=_default_callback_zip):
    """
    Zip up files, adding permissions when appropriate.
    """

    if not zip_file:
        zip_file = tempfile.mkstemp()[1]

    zfile = None
    try:
        zfile = ZipFile(zip_file, 'w', compression)
        for fi, (dest_path, src_path) in enumerate(files_dict.iteritems()):
            if callback:
                callback(src_path, fi, len(files_dict))
            # All platforms besides windows need permissions set.
            ext = os.path.splitext(dest_path)[1]
            if ext not in not_system_specific_scripts(system="windows"):
                zfile.write(src_path, arcname=dest_path)
            # Add with exec perms
            else:
                info = ZipInfo(dest_path)
                info.external_attr = 0775 << ((1 - is_osx()) * 16L) # give full access to included file
                with open(src_path, "r") as fh:
                    zfile.writestr(info, fh.read())
        zfile.close()
    finally:
        if zfile:
            zfile.close()

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
            os.chmod(os.path.realpath(dest_dir + "/" + afile), 0775)
