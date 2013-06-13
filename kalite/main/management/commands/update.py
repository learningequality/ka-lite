import git
import os
import glob
import stat
import platform
import shutil
import sys
import subprocess
import tempfile
import zipfile
from optparse import make_option
from zipfile import ZipFile, ZIP_DEFLATED

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

import settings


def call_outside_command_with_output(kalite_location, command, *args, **kwargs):
    
    # build the command
    cmd = (sys.executable,kalite_location + "/kalite/manage.py",command)
    for arg in args:
        cmd += (arg,)
    for key,val in kwargs.items():
        key = key.replace("_","-")
        prefix = "--" if command != "runcherrypyserver" else ""
        if isinstance(val,bool):
            cmd += ("%s%s" % (prefix,key),)
        else:
            cmd += ("%s%s=%s" % (prefix,key,str(val)),)

    if settings.DEBUG:
        print cmd
    
    # Execute the command, using subprocess/Popen
    cwd = os.getcwd()
    os.chdir(kalite_location + "/kalite")
    p = subprocess.Popen(cmd, shell=False, cwd=os.path.split(cmd[0])[0], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = p.communicate()
    os.chdir(cwd)
    
    if settings.DEBUG:
        if out[1]:
            print out[1]
        else:
            print out[0]
#        if out[1]:
#            import pdb; pdb.set_trace()
    return out + (1 if out[1] else 0,)
        
    
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
        make_option('-p', '--port',
            action='store',
            dest='port',
            default=8008,
            help='PORT where we can test KA Lite',
            metavar="PORT"),
        make_option('-i', '--interactive',
            action="store_true",
            dest="interactive",
            default=False,
            help="Display interactive prompts"),
        )


    def handle(self, *args, **options):

        # Callback for "weak" test--checks at least that the django project compiles (local_settings is OK)
        if len(args)==1 and args[0]== "test":
            print "Success!"
            exit(0)
        
        # Specified a repo
        if options.get("repo", None):
            self.update_via_git(options.get("repo", "."))
        
        # Specified a file
        elif options.get("zip_file", None):
            if not os.path.exists(options.get("zip_file")):
                raise CommandError("Specified zip file does not exist: %s" % options.get("zip_file"))
            self.update_via_zip(options.get("zip_file"), options.get("interactive"))
            
        # Without params, if we detect a git repo, try git
        elif false and os.path.exists(settings.PROJECT_PATH + "/../.git"):
            self.update_via_git(options.get("repo"))
        
        # No params, no git repo: try to get a file online.
        else:
            zip_file = tempname.tmpsname()[1]
            for url in ["https://github.com/learningequality/ka-lite/archive/master.zip",
                        "http://%s/download/kalite/%s/%s/" % (settings.CENTRAL_SERVER_HOST, options["platform"], options["locale"])]:
                self.log.info("Downloading repo snapshot to %s from %s" % (url))
                try:
                    urllib.urlretrieve(url, zip_file)
                    print "success @ %s" % url
                    break;
                except:
                    continue        

            self.update_via_zip(zip_file, options.get("interactive"))


        self.stdout.write("Update is complete!\n")
        
                

    def update_via_git(self, repo="."):
        print "Updating via git repo: %s" % repo
        self.stdout.write(git.Repo(repo).git.pull() + "\n")
        call_command("syncdb", migrate=True)


    def update_via_zip(self, zip_file, interactive=True):
        if not os.path.exists(zip_file):
            raise CommandError("Zip file doesn't exist")
            
        print "Updating via zip file: %s" % zip_file

        self.current_dir = os.path.realpath(settings.PROJECT_PATH + "/../")
        self.neighbor_dir = os.path.realpath(self.current_dir + "/../" + os.path.splitext(os.path.split(zip_file)[1])[0])
        
        # Prep
        self.print_header()
        self.get_dest_dir(interactive)
        self.get_move_videos(interactive)
        
        # Work
        self.extract_files(zip_file)
        self.copy_in_data()
        self.update_local_settings()
        self.move_video_files()
        
        # Validation & confirmation
        if platform.system()=="Windows":
            self.test_server_weak()
            self.move_to_final(interactive)
        else:
            self.test_server_full()
            self.move_to_final(interactive)
            self.start_server()

        self.print_footer()
        
    
    def print_header(self):
        """Start the output with some informative header"""
        print ""
        print "*"*50
        print "*"
        print "* Upgrade KA Lite!"
        print "*"
        print "*\tCurrent install directory: %s" % self.current_dir


    def get_dest_dir(self, interactive=True):
        """Prompt for a destination, providing some easy options"""
        
        if interactive:
            print "*"
            print "* Where would you like to install your KA Lite ugrade to?"
            print "*\t0 : replace the current installation (%s)" % self.current_dir
            print "*\t1 : %s" % self.neighbor_dir
            print "*\tOr any other path"
            print "*"

        dest_dir = "" if interactive else self.current_dir
        working_dir = "" if interactive else tempfile.mkdtemp()
        while not dest_dir:
            dest_dir=raw_input("*\tEnter a number, or path: ").strip()
            
            if dest_dir=="0":
                dest_dir = self.current_dir
                working_dir = tempfile.mkdtemp()
            elif dest_dir=="1":
                dest_dir = self.neighbor_dir
                working_dir = tempfile.mkdtemp() if not settings.DEBUG else dest_dir # speedup for debug
            elif dest_dir=="2":
                dest_dir = tempfile.mkdtemp()
                working_dir = dest_dir
            else:
                working_dir = tempfile.mkdtemp()
            if os.path.exists(dest_dir):# and dest_dir != self.current_dir:
                ans = ""
                while ans not in ["y","n"]:
                    ans = raw_input("*\tDestination directory exists; replace? [y/n]: ").strip().lower()
                if ans=="y":
                    break         # got it!
                else:   
                    dest_dir = "" # try again
            
        self.dest_dir = dest_dir
        self.working_dir = working_dir
        
        
    def get_move_videos(self, interactive=True):
        """See whether the user wants to move video files, or to keep them in the existing location.
        
        Note that we have some meaningful cases where we don't need to prompt the user to set this."""
        
        self.videos_inside_install = -1 != settings.CONTENT_ROOT.find(self.current_dir)
        if not self.videos_inside_install:
            self.move_videos = "n" # videos exist outside of this install, continue that way
        
        elif self.dest_dir == self.current_dir or not interactive:
            self.move_videos = "y" # You HAVE to move videos

        # Ask if we want to move videos
        else:
            move_videos = ""
            while move_videos not in ["y","n"]:
                move_videos = raw_input("*\tMove movie files from old install to new? [y/n]: ").strip().lower()   
                
            self.move_videos = move_videos
                     
                     

    def extract_files(self,zip_file):  
        """Extract all files to a temp location"""
        
        print "*"
        print "* temp location == %s" % self.working_dir
        print "* Extracting all files to a temporary location; please wait...",
        sys.stdout.flush()
    
        # Speedup debug by not extracting
        if settings.DEBUG and os.path.exists(self.working_dir + "/install.sh"):
            print "** NOTE ** NOT EXTRACTING IN DEBUG MODE"
            return
                        
        if not os.path.exists(self.working_dir):
            os.mkdir(self.working_dir)
        
        if not zipfile.is_zipfile(zip_file):
            raise CommandError("bad zip file")

        zip = ZipFile(zip_file, "r")
            
        nfiles = len(zip.namelist())
        for fi,afile in enumerate(zip.namelist()):
            
            # print progress
            if fi>0 and fi%round(nfiles/10)==0:
                pct_done = round(100.*(fi+1.)/nfiles)
                print " %d%%" % pct_done,
                sys.stdout.flush()
                    
            zip.extract(afile, path=self.working_dir)
            # If it's a unix script, give permissions to execute
#            if os.path.splitext(os.path.split(afile)[1])[1] == ".sh":
#                os.chmod(self.working_dir + "/" + afile, 0755)
            # We need to be able to run scripts, so set perms properly
            if os.path.splitext(afile)[1] == ".sh":
                os.chmod(os.path.realpath(self.working_dir + "/" + afile), 0777)    
                print "\tChanging perms on script %s" % os.path.realpath(self.working_dir + "/" + afile)
            
        print ""
        
        if not os.path.exists(self.working_dir + "/kalite/"):
            subdirs = os.listdir(self.working_dir)
            if len(subdirs)!=1:
                raise CommandError("Expected %s to exist, but it doesn't.  Unknown failure in extraction; exiting." % (self.working_dir + "/kalite/"))

            # Must be a download from git directly.
            else:
                self.working_dir += "/" + subdirs[0] + "/"
                print "Note: found a git-based package.  Updating working dir to %s" % self.working_dir
        

    def copy_in_data(self):
        """Copy over sqlite3 database, then run syncdb"""
        
        # Copy over data
        if settings.DATABASES['default']['ENGINE']!='django.db.backends.sqlite3':
            raise NotImplementedError("No code for doing a SQL-SQL transfer.")
        print "* Copying over database to the server update location"
        shutil.copy(settings.DATABASES['default']['NAME'], os.path.realpath(self.working_dir + "/kalite/database/data.sqlite"))
        
        # Run the syncdb
        print "* Syncing database...",
        out = call_outside_command_with_output(self.working_dir, "migrate", delete_ghost_migrations=True)
        out = call_outside_command_with_output(self.working_dir, "syncdb", migrate=True)
        #if out[2] or out[1]:
        #    raise CommandError("\n\tError syncing data[%d]: %s" % (out[2], out[1] if out[1] else out[0]))
        #else:
        print ""
            
        # Run the migration
        print "* Migrating app schemas...",
        for app in ["securesync", "main", "config"]:
            print " %s" % app,
            out = call_outside_command_with_output(self.working_dir, "schemamigration", app, auto=True)

            if -1 != out[1].find("You can now apply this migration with:"):
                out = call_outside_command_with_output(self.working_dir, "migrate", app)
                print "(applied)",

            # schemamigration has this bad habit of dumping a bunch of stuff to stderr.
            elif -1 != out[1].find("Nothing seems to have changed"):
                print "(none)",
            
            else:
                raise CommandError("\n\tError migrating app %s [%d]: %s" % (app, out[2], out[1] if out[1] else out[0]))    
        print ""
            
            
    def move_video_files(self):
        """If necessary (determined previously), move video files on disk.  
        Otherwise, write into local_settings.""" 
        
        # Move over videos
        if self.move_videos=="y":
            if os.path.exists(settings.CONTENT_ROOT):
                video_files = set(glob.glob(settings.CONTENT_ROOT + '*')) - set((settings.CONTENT_ROOT + "note.txt",)) 
            else:
                video_files = {}
            print "* Moving over %d files (videos and thumbnails)" % len(video_files)
            if not os.path.exists(self.working_dir + "/content/"):
                os.mkdir(self.working_dir + "/content/")
            for video_file in video_files:
                shutil.move(video_file, self.working_dir + "/content/" + os.path.split(video_file)[1])
                
        else: # write (append)
            fh = open(self.working_dir + "/kalite/local_settings.py", "a")
            fh.write("\nCONTENT_ROOT = '%s'\n" % settings.CONTENT_ROOT)
            fh.close()


    def update_local_settings(self):    
        """Combine the old and new local settings (put new last, so that they have precedence)"""

        print "* Updating local settings"
                
        # Include the old local_settings.py
        cur_ls_file = settings.PROJECT_PATH + "/local_settings.py"
        if os.path.exists(cur_ls_file):
            fh = open(cur_ls_file, "r")
            cur_ls = fh.read()
            fh.close()
        else:
            cur_ls = ""
            
        # Read any new
        new_ls_file = self.working_dir + "/kalite/local_settings.py"
        if os.path.exists(new_ls_file):    
            fh = open(new_ls_file, "r")
            new_ls = fh.read()
            fh.close()
        else:
            new_ls = ""
        
        # Create combination  
        fh = open(self.working_dir + "/kalite/local_settings.py", "w")
        fh.write(cur_ls + "\n" + new_ls)
        fh.close()
    
    def test_server_weak(self):
#        out = call_outside_command_with_output(self.working_dir, "runcherrypyserver", host="0.0.0.0", port=8008, threads=1)
        print "* Testing the new server (simple)"

        out = call_outside_command_with_output(self.working_dir, "update", "test")
        if 0 != out[0].find("Success!"):
            raise CommandError(out[1] if out[1] else out[0])
            
            
    def test_server_full(self):
        """Stop the old server.  Start the new server."""
        
        print "* Testing the new server (full)"
        
        # Stop the old server
        stop_cmd = self.get_shell_script("serverstop*", location=self.current_dir + "/kalite/")
        if stop_cmd:
            try:
                p = subprocess.Popen([stop_cmd], shell=False, cwd=os.path.split(stop_cmd)[0], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out = p.communicate()
                if out[1]:
                    raise CommandError(out[1])
            except Exception as e:
                print "Failed stopping the old server: %s" % str(e)
                
        
        # Start the server to validate
        start_cmd = self.get_shell_script("serverstart*", location=self.working_dir + "/kalite/")
        try:
            p = subprocess.Popen([start_cmd], shell=False, cwd=os.path.split(start_cmd)[0], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out = p.communicate()
            if out[1]:
                raise CommandError(out[1])
        except Exception as e:
            print "Failed starting the new server: %s" % str(e)
        
        # Stop the server
        stop_cmd = self.get_shell_script("serverstop*", location=self.working_dir + "/kalite/")
        if stop_cmd:
            try:
                p = subprocess.Popen([stop_cmd], shell=False, cwd=os.path.split(stop_cmd)[0], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out = p.communicate()
                if out[1]:
                    raise CommandError(out[1])
            except Exception as e:
                print "Failed stopping the new server: %s" % str(e)

    
    def move_to_final(self, interactive=True):
        """Confirm the move to the new location"""
        
        # Double-check if destroying old install
        if self.dest_dir == self.current_dir:
            ans = "" if interactive else "y"
            while ans.lower() not in ["y","n"]:
                ans = raw_input("* Server setup verified; complete by moving to the final destination? [y/n]: ").strip()
            if ans=="n":
                print "**** Aborting update; new server (with content) can be found at %s" % self.working_dir  
                exit()
             
        # OK, don't actually kill it--just move it   
        if os.path.exists(self.dest_dir):
            tempdir = tempfile.mkdtemp()
            print "* Moving old directory to a temporary location..."
            try:
                shutil.move(self.dest_dir, tempdir)

                # Move to the final destination
                print "* Moving new installation to final position."
                shutil.move(self.working_dir, self.dest_dir)
                
            except Exception as e:
                print "***** ERROR: Failed to move: %s to %s:" % (self.dest_dir, tempdir)
                print "*****        '%s'" % str(e)
                print "***** Trying to copy contents into dest_dir"
                copy_success = 0
                for root, dirs, files in os.walk(self.working_dir):
                    if 0==root.find(self.working_dir):
                        relpath = root[len(self.working_dir):]
                    else:
                        relpath = root[1:]
                        
                    for d in dirs:
                        drelpath = relpath + "/" + d
                        if not os.path.exists(self.dest_dir + drelpath):
                            print "Created directory %s%s" % (self.dest_dir, drelpath)
                            os.mkdir(self.dest_dir + drelpath)
                            
                    for f in files:
                        try:
                            frelpath = "/" + relpath + "/" + f
                            shutil.copyfile(self.working_dir + frelpath, self.dest_dir + frelpath)
                            copy_success += 1#print "copied %s%s to %s%s" % (self.working_dir, frelpath, self.dest_dir, frelpath)
                        except:
                            print "**** failed to copy %s%s" % (self.working_dir, frelpath)
                print "* Successfully copied %d files into final directory" % copy_success
                #os.remove(self.working_dir)
 
 
    def start_server(self):
        """ """
        
        print "* Starting the server"
         
        # Start the server to validate
        start_cmd = self.get_shell_script("serverstart*", location=self.current_dir + "/kalite/")
        p = subprocess.Popen([start_cmd], shell=False, cwd=os.path.split(start_cmd)[0], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = p.communicate()
        if out[1]:
            raise CommandError(out[1])
        
        str = "The server should now be accessible locally at"
        idx = out[0].find(str)
        addr = out[0][idx+2+len(str):]#out[0].find("\n",idx)]
        
        print "* Server accessible @ %s" % addr


    def print_footer(self):
        print "*"
        print "* Installation complete!"
        print "*"*50
        
    
    def get_shell_script(self, cmd_glob, location=None):
        if not location:
            location = self.working_dir + '/kalite'
        if platform.system() == "Windows":
            cmd_glob += ".bat"
        else:
            cmd_glob += ".sh"
            
        # Find the command
        cmd = glob.glob(location + "/" + cmd_glob)
        if len(cmd) > 1:
            raise CommandError("Multiple commands found (%s)?  Should choose based on platform, but ... how to do in Python?  Contact us to implement this!" % cmd_glob)
        elif len(cmd)==1:
            cmd = cmd[0]
        else:
            cmd = None#raise CommandError("No command found? (%s)" % cmd_glob)
        return cmd
