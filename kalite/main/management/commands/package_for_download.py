import logging
import os
import shutil
import platform
import tempfile
from optparse import make_option
from zipfile import ZipFile, ZIP_DEFLATED

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

import settings
import version


def file_in_platform(file_path, platform):
    """Logic on whether to include or exclude a file, 
    based on the requested platform and the file's name (including path)"""
    
    ext = os.path.splitext(file_path)[1]
    if platform=="windows":
        return ext not in [".sh",]
    elif platform=="all":
        return True
    else:
        return ext not in [".vbs", ".bat"]
        

def file_in_server_type(file_path, server_type):
    """Logic on whether to include or exclude a file, 
    based on the requested server type and it's name (including path)"""
    return True


def select_package_dirs(dirnames, key_base, **kwargs):
    """Choose which directories to include/exclude, 
    based on the "key-base", which is essentially the relative path from the ka-lite project"""
    base_name = os.path.split(key_base)[1]

    if key_base=="":
        in_dirs = {'docs', 'kalite', 'locale', 'python-packages'}
        
    # ONLY include files for the particular locale
    elif (base_name=="locale" or base_name=="localflavor") and "locale" in kwargs and kwargs['locale']:
            in_dirs = {kwargs['locale']}

    else:
        in_dirs = set(dirnames) - {'loadtesting', 'tests', 'test', 'testing','tmp', 'selenium', 'werkzeug', 'postmark'}
        if "server_type" in kwargs and kwargs['server_type']!="central":
            in_dirs -= {"central", "landing-page"}

    return in_dirs
    
def decorate_file_dict(files_dict):
    """Given a dictionary of dictionaries, of files to include (key=src path, dict=options, including dest path), 
    decorate that dictionary with whatever attributes we want (file size? Hash? Explicit dest path when missing?).
    
    Would be used in the future for creating a manifest file, describing all known files.
    """
    for file,fdict in files_dict.items():
        if "dest_path" not in fdict:
            raise Exception("Must always set 'dest_path'; failed for file %s" % file)
        
    return files_dict

def file_in_ok_set(file_path):
    """Generic filter to eliminate particular filenames and extensions.
    
    Note: explicitly keep out local_settings"""
    
    name = os.path.split(file_path)[1]
    ext = os.path.splitext(file_path)[1]
    return (ext not in [".pyc",".sqlite",".zip"]) and (name not in ["local_settings.py", ".gitignore", "tests.py", "faq",".DS_Store"])


def recursively_add_files(dirpath, files_dict=dict(), key_base="", **kwargs):
    """Recurses into the directories of dirpath to add files to files_dict.
    
    files_dict: key is source path, value is a dict including dest_path (in archive)
    key_base:the relative path from the ka-lite project; used to identify 
             the location in the project when including/excluding files/dirs
    """
    
    for (_, dirnames, filenames) in os.walk(dirpath):
    
        # 
        in_dirs = select_package_dirs(dirnames, key_base=key_base, **kwargs)
        
        # Base case: loop all files in this directory
        for f in filenames:
            file_path = dirpath+"/"+f
            if not file_in_ok_set(file_path=file_path):
                continue
            elif "server_type" in kwargs and kwargs["server_type"] and not file_in_server_type(file_path=file_path, server_type=kwargs["server_type"]):
                continue
            elif "platform" in kwargs and kwargs["platform"] and not file_in_platform(file_path=file_path, platform=kwargs["platform"]):
                continue

            # Made it through!  Include in the package
            files_dict[dirpath+"/"+f] = {"dest_path": f if key_base=="" else key_base+"/"+f}

        # Recursive case: loop all subdirectories
        for d in in_dirs:
            files_dict = recursively_add_files(dirpath=dirpath+"/"+d, files_dict=files_dict, key_base=key_base+"/"+d, **kwargs)
        
        break        # lazy to use walk; just break

    
    return files_dict

def create_local_settings_file(location, server_type="local", locale=None, central_server=None):
    """Create an appropriate local_settings file for the installable server."""
    
    fil = tempfile.mkstemp()[1]
    
    if settings.CENTRAL_SERVER != ("central"==server_type): #mismatch
        pass
        
    # duplicate local_settings when packaging from a local server
    elif os.path.exists(location):
        shutil.copy(location, fil) 

    # Can steal it
    central_server = central_server or server.CENTRAL_SERVER_HOST
        
    with open(fil,"a") as ls: #append, to keep those settings, but override SOME
        ls.write("\n") # never trust the previous file ended with a newline!
        if settings.DEBUG:
            ls.write("DEBUG = %s\n" % str(settings.DEBUG)) # need to make sure that production clients never see this.
        ls.write("CENTRAL_SERVER = %s\n" % (server_type=="central"))
        if locale:
            ls.write("LANGUAGE_CODE = '%s'\n" % locale)
        if central_server:
            ls.write("CENTRAL_SERVER_HOST = '%s'\n" % central_server)
            ls.write("CENTRAL_SERVER_DOMAIN = '%s'\n" % central_server)
            ls.write("SECURESYNC_PROTOCOL = '%s'\n" % "http" if settings.DEBUG else "https") # need to make DEBUG is set properly
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
        make_option('-c', '--central-server',
            action='store',
            dest='central_server',
            default=None,
            help='hostname (with port) of central server'),

        make_option('-f', '--file',
            action='store',
            dest='file',
            default="__default__",
            help='FILE to save zip to',
            metavar="FILE"),
        )

    def command_error(self, msg):
        self.stderr.write("%s\n" % msg)
        if __name__=="__main__":
            exit(1)
        else:
            raise Exception(msg)
        
    def handle(self, *args, **options):
    #try:
        options['platform'] = options.get('platform','').lower()
    
        if options['platform'] not in ["all","linux","macos","darwin","windows"]:
            self.command_error("Unrecognized platform: %s; will include ALL files." % options['platform'])
        
        # Step 1: recursively add all static files
        kalite_base = os.path.realpath(settings.PROJECT_PATH + "/../")
        files_dict = recursively_add_files(dirpath=kalite_base, locale=options["locale"], server_type=options['server_type'], platform=options['platform'])

        # Step 2: Generate and add all dynamic content (database json info, server)
        ls_loc = os.path.realpath(kalite_base+"/kalite/local_settings.py")
        ls_file = create_local_settings_file(location=ls_loc, server_type=options['server_type'], locale=options['locale'], central_server=options['central_server'])
        files_dict[ls_file] = { "dest_path": "kalite/local_settings.py" }
    
        # Step 3: Decorate
        files_dict = decorate_file_dict(files_dict)
    
        # Step 4: package into a zip file
        fil = tempfile.mkstemp()[1]
        with ZipFile(fil, "w", ZIP_DEFLATED) as zfile:
            for srcpath,fdict in files_dict.items():
                if options['verbosity']>=1:
                    print "Adding to zip: %s" % srcpath
                try:
                    zfile.write(srcpath, arcname=fdict["dest_path"])
                except Exception as e:
                    self.stderr.write("Failed to write %s to %s: %s\n" % (str(srcpath), str(fdict["dest_path"]), str(e)))
                     
        # Step 5: output
        if options['file']=="__default__":
            options['file'] = create_default_archive_filename(options)
        shutil.move(fil, options['file']) # move the archive
        #except Exception as e:
        #    raise e
        #    self.command_error(str(e))