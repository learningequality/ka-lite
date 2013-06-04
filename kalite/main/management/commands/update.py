import git
import os
import glob
import platform
import shutil
import sys
import subprocess
import tempfile
import zipfile

from optparse import make_option
from zipfile import ZipFile, ZIP_DEFLATED

from django.core.management.base import BaseCommand, CommandError

import settings
settings.DEBUG = False

def fixBadZipfile(zipFile):  
    f = open(zipFile, 'r+b')  
    data = f.read()  
    pos = data.find('\x50\x4b\x05\x06') # End of central directory signature  
    if (pos > 0):  
        #("Trancating file at location " + str(pos + 22)+ ".")  
        f.seek(pos + 22)   # size of 'ZIP end of central directory record' 
        f.truncate()  
        f.close()  
    else:  
        raise Exception("# raise error, file is truncated  ")
         
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
        )


    def command_error(self, msg):
        print msg
        if settings.DEBUG:
            import pdb; pdb.set_trace()
        exit(1)
        
    def handle(self, *args, **options):
    
        # Callback for "weak" test--checks at least that the django project compiles (local_settings is OK)
        if len(args)==1 and args[0]== "test":
            print "Success!"
            exit(0)
            
        if options.get("repo", None):
            self.update_via_git(options.get("repo"))
            
        elif options.get("zip_file", None):
            if not os.path.exists(options.get("zip_file")):
                self.command_error("Specified zip file does not exist: %s" % options.get("zip_file"))
            self.update_via_zip(options.get("zip_file"))
            
        # Without params, default to same as before (git)
        elif not args and not options:
            self.update_via_git(options.get("repo"))
        
        else:
            self.command_error("Please specify a zip file.")
            
            """# Search for a zip
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
                        continue"""
        
        self.stdout.write("Update is complete!\n")
        
                

    def update_via_git(self, repo="."):
        print "Updating via git repo: %s" % repo
        self.stdout.write(git.Repo(repo).git.pull() + "\n")
        call_command("syncdb", migrate=True)


    def update_via_zip(self, zip_file):
        if not os.path.exists(zip_file):
            self.command_error("Zip file doesn't exist")
            
        print "Updating via zip file: %s" % zip_file

        self.current_dir = os.path.realpath(settings.PROJECT_PATH + "/../")
        self.neighbor_dir = os.path.realpath(self.current_dir + "/../" + os.path.splitext(os.path.split(zip_file)[1])[0])
        
        # Prep
        self.print_header()
        self.prompt_dest_dir()
        self.prompt_move_videos()
        
        # Work
        self.extract_files(zip_file)
        self.copy_in_data()
        self.update_local_settings()
        self.move_video_files()
        
        # Validation & confirmation
        if platform.system()=="Windows":
            self.test_server_weak()
            self.confirm_move()
        else:
            self.test_server_full()
            self.confirm_move()
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


    def prompt_dest_dir(self):
        """Prompt for a destination, providing some easy options"""
        
        print "*"
        print "* Where would you like to install your KA Lite ugrade to?"
        print "*\t0 : replace the current installation (%s)" % self.current_dir
        print "*\t1 : %s" % self.neighbor_dir
        print "*\tOr any other path"
        print "*"

        dest_dir = ""
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
        
        
    def prompt_move_videos(self):
        """See whether the user wants to move video files, or to keep them in the existing location.
        
        Note that we have some meaningful cases where we don't need to prompt the user to set this."""
        
        self.videos_inside_install = -1 != settings.CONTENT_ROOT.find(self.current_dir)
        if not self.videos_inside_install:
            self.move_videos = "n" # videos exist outside of this install, continue that way
        
        elif self.dest_dir == self.current_dir:
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
        print "* Extracting all files to a temporary location; please wait...",
        sys.stdout.flush()

        # Speedup debug by not extracting
        if settings.DEBUG and os.path.exists(self.working_dir):
            print ""
            return
                        
        if not os.path.exists(self.working_dir):
            os.mkdir(self.working_dir)
        
        if not zipfile.is_zipfile(zip_file):
            self.command_error("bad zip file")

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
            if os.path.splitext(os.path.split(afile)[1])[1] == ".sh":
                os.chmod(self.working_dir + "/" + afile, 0755)
        print ""
        
    
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
        if out[2] or out[1]:
            self.command_error("\n\tError syncing data[%d]: %s" % (out[2], out[1] if out[1] else out[0]))
        else:
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
                self.command_error("\n\tError migrating app %s [%d]: %s" % (app, out[2], out[1] if out[1] else out[0]))    
        print ""
            
            
    def move_video_files(self):
        """If necessary (determined previously), move video files on disk.  
        Otherwise, write into local_settings.""" 
        
        # Move over videos
        if self.move_videos=="y":
            import pdb; pdb.set_trace()
            video_files = set(glob.glob(settings.CONTENT_ROOT + '*')) - set((settings.CONTENT_ROOT + "note.txt",)) 
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
            self.command_error(out[1] if out[1] else out[0])
            
            
    def test_server_full(self):
        """Stop the old server.  Start the new server."""
        
        print "* Testing the new server (full)"
        
        # Stop the old server
        stop_cmd = self.get_shell_script("serverstop*", location=self.current_dir + "/kalite/")
        if stop_cmd:
            p = subprocess.Popen([stop_cmd], shell=False, cwd=os.path.split(stop_cmd)[0], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out = p.communicate()
            if out[1]:
                command_error(out[1])

        
        # Start the server to validate
        start_cmd = self.get_shell_script("serverstart*", location=self.working_dir + "/kalite/")
        p = subprocess.Popen([start_cmd], shell=False, cwd=os.path.split(start_cmd)[0], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = p.communicate()
        if out[1]:
            command_error(out[1])
        
        # Stop the server
        stop_cmd = self.get_shell_script("serverstop*", location=self.working_dir + "/kalite/")
        if stop_cmd:
            p = subprocess.Popen([stop_cmd], shell=False, cwd=os.path.split(stop_cmd)[0], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out = p.communicate()
            if out[1]:
                command_error(out[1])

    
    def confirm_move(self):
        """Confirm the move to the new location"""
        
        # Double-check if destroying old install
        if self.dest_dir == self.current_dir:
            ans = ""
            while ans.lower() not in ["y","n"]:
                ans = raw_input("* Server setup verified; complete by moving to final destination? [y/n]: ").strip()
            if ans=="n":
                print "**** Aborting update; new server (with content) can be found at %s" % self.working_dir  
                exit()
             
        # OK, don't actually kill it--just move it   
        if os.path.exists(self.dest_dir):
            tempdir = tempfile.mkdtemp()
            shutil.move(self.dest_dir, tempdir)
            print "*\tOld install moved to temp location (%s); OS will delete for you soon!" % tempdir
        
        # Move to the final destination
        shutil.move(self.working_dir, self.dest_dir)


    def start_server(self):
        """ """
        
        print "* Starting the server"
         
        # Start the server to validate
        start_cmd = self.get_shell_script("serverstart*", location=self.current_dir + "/kalite/")
        p = subprocess.Popen([start_cmd], shell=False, cwd=os.path.split(start_cmd)[0], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = p.communicate()
        if out[1]:
            self.command_error(out[1])
        
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
            self.command_error("Multiple commands found (%s)?  Should choose based on platform, but ... how to do in Python?  Contact us to implement this!" % cmd_glob)
        elif len(cmd)==1:
            cmd = cmd[0]
        else:
            cmd = None#self.command_error("No command found? (%s)" % cmd_glob)
        return cmd
        

    
    