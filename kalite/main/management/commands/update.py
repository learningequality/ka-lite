import git
import os
import glob
import shutil
import subprocess
import tempfile

from optparse import make_option
from zipfile import ZipFile, ZIP_DEFLATED

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

import settings


class Command(BaseCommand):
    help = "Create a zip file with all code, that can be unpacked anywhere."

    option_list = BaseCommand.option_list + (
        make_option('-r', '--repo',
            action='store',
            dest='repo',
            default=None,
            help='Git REPO to pull from',
            metavar="REPO"),
        make_option('-f', '--file',
            action='store',
            dest='zip_file',
            default=None,
            help='FILE to unzip from',
            metavar="FILE"),
        )


    def command_error(self, msg):
        print msg
        exit(1)
        
    def handle(self, *args, **options):
        if options.get("repo", None):
            self.update_via_git(options.get("repo"))
        elif options.get("zip_file", None):
            if not os.path.exists(options.get("zip_file")):
                self.command_error("Specified zip file does not exist: %s" % options.get("zip_file"))
            self.update_via_zip(options.get("zip_file"))
        else:
            # Search for a zip
            files = ()
            for search_path in [settings.PROJECT_PATH+"/../", settings.PROJECT_PATH]:
                files += tuple(glob.glob('*.zip'))
            
            if len(files)==0:
                self.update_via_git()
            elif len(files)==1:
                self.update_via_zip(files[0])
            else:
                for f in files:
                    try:
                        self.update_via_zip(f)
                        break
                    except:
                        import pdb; pdb.set_trace()
                        continue
        
        self.stdout.write("Update is complete!\n")
        
        
    def update_via_zip(self, zip_file):
        print "Updating via zip file: %s" % zip_file
        
        # Should prompt for a destination (default to same directory as existing ka-lite, but with zip name)
        current_dir = os.path.realpath(settings.PROJECT_PATH + "/../")
        neighbor_dir = os.path.realpath(current_dir + "/../" + os.path.splitext(os.path.split(zip_file)[1])[0])
        print ""
        print "*"*50
        print "*"
        print "* Upgrade KA Lite!"
        print "*"
        print "*\tCurrent install directory: %s" % current_dir
        print "*"
        print "* Where would you like to install your KA Lite ugrade to?"
        print "*\t0 : replace the current installation (%s)" % os.path.realpath(settings.PROJECT_PATH + "/../")
        print "*\t1 : %s" % neighbor_dir
        print "*\tOr any other path"
        print "*"
        
        dest_dir = ""
        while not dest_dir:
            dest_dir=raw_input("*\tEnter a number, or path: ").strip()
            
            if dest_dir=="0":
                dest_dir = os.path.realpath(settings.PROJECT_PATH + "/../")
                working_dir = tempfile.mkdtemp()
            elif dest_dir=="1":
                dest_dir = neighbor_dir
                working_dir = tempfile.mkdtemp()
            elif dest_dir=="2":
                dest_dir = tempfile.mkdtemp()
                working_dir = dest_dir
                
            if os.path.exists(dest_dir):
                ans = ""
                while ans not in ["y","n"]:
                    ans = raw_input("*\tDestination directory exists; replace? [y/n]: ").strip().lower()
                if ans=="y":
                    break         # got it!
                else:   
                    dest_dir = "" # try again

        move_videos = ""
        while move_videos not in ["y","n"]:
            move_videos = raw_input("*\tMove movie files to %s? [y/n]: " % (dest_dir + "/content/")).strip().lower()
            
            
        # Extract all files to a new location
        print "*"
        print "* Extracting all files to %s; please wait..." % working_dir
        if not os.path.exists(working_dir):
            os.mkdir(working_dir)
        zip = ZipFile(open(zip_file, "r"))
        for afile in zip.namelist():
            zip.extract(afile, path=working_dir)
            if os.path.splitext(os.path.split(afile)[1])[1] == ".sh":
                os.chmod(working_dir + "/" + afile, 0755)
        
        # Copy over data
        if settings.DATABASES['default']['ENGINE']!='django.db.backends.sqlite3':
            raise NotImplementedError("No code for doing a SQL-SQL transfer.")
        print "* Copying over database to %s" % working_dir
        shutil.copy(settings.DATABASES['default']['NAME'], working_dir + "/kalite/database/data.sqlite")
        
        # Run the syncdb
        #call_command("syncdb", migrate=True)

        # Move over videos
        if move_videos=="y":
            video_files = glob.glob(settings.CONTENT_ROOT + '*')
            print "* Moving over %d files (videos and thumbnails)" % len(video_files)
            if not os.path.exists(working_dir + "/content/"):
                os.mkdir(working_dir + "/content/")
            for video_file in video_files:
                shutil.move(video_file, working_dir + "/content/" + os.path.split(video_file)[1])
        else:
            fh = open(working_dir + "/kalite/local_settings.py", "w")
            fh.write("\nCONTENT_ROOT = '%s'\n" % settings.CONTENT_ROOT)
            fh.close()
            
        # Include the old local_settings.py
        fh = open(settings.PROJECT_PATH + "/local_settings.py", "r")
        cur_ls = fh.read()
        fh.close()
        
        fh = open(working_dir + "/kalite/local_settings.py", "r")
        new_ls = fh.read()
        fh.close()
        
        fh = open(working_dir + "/kalite/local_settings.py", "w")
        fh.write(cur_ls + "\n" + new_ls)
        fh.close()
        
        # Start the server to validate
        start_cmd = glob.glob(working_dir + '/kalite/serverstart*')
        if len(start_cmd) != 1:
            Exception("?")
        subprocess.Popen(start_cmd, shell=True, cwd=os.path.split(start_cmd[0])[0]).communicate()

        # Stop the server
        stop_cmd = glob.glob(working_dir + '/kalite/serverstop*')
        if len(stop_cmd) != 1:
            Exception("?")
        subprocess.Popen(stop_cmd, shell=True, cwd=os.path.split(stop_cmd[0])[0]).communicate()

        
        # Move to the final destination
        ans = ""
        while ans.lower() not in ["y","n"]:
            ans = raw_input("* Server setup verified; complete by moving to final destination? [y/n]: ").strip()
        if ans=="n":
            print "**** Aborting update; new server (with content) can be found at %s" % working_dir    
        else:
            tempdir = tempfile.mkdtemp()
            if os.path.exists(dest_dir):
                shutil.move(dest_dir, tempdir)
                print "*\tOld install is now available at temp location (%s) and will be deleted by the OS in the future." % tempdir
            shutil.move(working_dir, dest_dir)
        
    
    def update_via_git(self, repo="."):
        print "Updating via git repo: %s" % repo
        self.stdout.write(git.Repo(repo).git.pull() + "\n")
        call_command("syncdb", migrate=True)
    