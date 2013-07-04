import git
import os
import glob
import platform
import shutil
import sys
import subprocess
import tempfile
import urllib
import zipfile
from optparse import make_option
from zipfile import ZipFile, ZIP_DEFLATED

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

import settings


def call_outside_command_with_output(kalite_location, command, *args, **kwargs):
    """
    Runs call_command for a KA Lite installation at the given location,
    and returns the output.
    """

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

    settings.LOG.debug(cmd)

    # Execute the command, using subprocess/Popen
    cwd = os.getcwd()
    os.chdir(kalite_location + "/kalite")
    p = subprocess.Popen(cmd, shell=False, cwd=os.path.split(cmd[0])[0], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = p.communicate()
    os.chdir(cwd)

    settings.LOG.debug(out[1] if out[1] else out[0])

    # tuple output of stdout, stderr, and exit code
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
            dest='test_port',
            default=9157,  # 'Random' test port.  Hopefully open!
            help='PORT where we can test KA Lite',
            metavar="PORT"),
        make_option('-i', '--interactive',
            action="store_true",
            dest="interactive",
            default=False,
            help="Display interactive prompts"),
        )


    def handle(self, *args, **options):

        if len(args)==1 and args[0]== "test":
            # Callback for "weak" test--checks at least that the django project compiles (local_settings is OK)
            sys.stdout.write("Success!\n")
            exit(0)

        if options.get("repo", None):
            # Specified a repo
            self.update_via_git(**options)

        elif options.get("zip_file", None):
            # Specified a file
            if not os.path.exists(options.get("zip_file")):
                raise CommandError("Specified zip file does not exist: %s" % options.get("zip_file"))
            self.update_via_zip(**options)

        elif os.path.exists(settings.PROJECT_PATH + "/../.git"):
            # Without params, if we detect a git repo, try git
            self.update_via_git(**options)

        elif len(args) > 1:
            raise CommandError("Too many command-line arguments.")

        elif len(args) == 1:
            # Specify zip via first command-line arg
            if options['zip_file'] is not None:
                raise CommandError("Cannot specify a zipfile as unnamed and named command-line arguments at the same time.")
            options['zip_file'] = args[0]
            self.update_via_zip(**options)

        else:
            # No params, no git repo: try to get a file online.
            zip_file = tempfile.mkstemp()[1]
            for url in ["https://github.com/learningequality/ka-lite/archive/master.zip",
                        "http://%s/download/kalite/%s/%s/" % (settings.CENTRAL_SERVER_HOST, platform.system().lower(), "all")]:
                settings.LOG.info("Downloading repo snapshot from %s to %s" % (url, zip_file))
                try:
                    urllib.urlretrieve(url, zip_file)
                    sys.stdout.write("success @ %s\n" % url)
                    break;
                except Exception as e:
                    settings.LOG.debug("Failed to get zipfile from %s: %s" % (url, e))
                    continue

            self.update_via_zip(zip_file=zip_file, **options)


        self.stdout.write("Update is complete!\n")



    def update_via_git(self, repo=".", *args, **kwargs):
        # Step 1: update via git repo
        sys.stdout.write("Updating via git repo: %s\n" % repo)
        self.stdout.write(git.Repo(repo).git.pull() + "\n")
        call_command("syncdb", migrate=True)


    def update_via_zip(self, zip_file, interactive=True, test_port=8008, *args, **kwargs):
        if not os.path.exists(zip_file):
            raise CommandError("Zip file doesn't exist")
        if not self.kalite_is_installed():
            raise CommandError("KA Lite not yet installed; cannot update.  Please install KA Lite first, then update.\n")

        sys.stdout.write("Updating via zip file: %s\n" % zip_file)

        # current_dir === base dir for current installation
        self.current_dir = os.path.realpath(settings.PROJECT_PATH + "/../")

        # Prep
        self.print_header()
        self.get_dest_dir(
            zip_name=os.path.splitext(os.path.split(zip_file)[1])[0],
            interactive=interactive
        )
        self.get_move_videos(interactive)

        # Work
        self.extract_files(zip_file)
        self.copy_in_data()
        self.update_local_settings()
        self.move_video_files()

        # Validation & confirmation
        if platform.system() == "Windows":  # In Windows. serverstart is not async
            self.test_server_weak()
        else:
            self.test_server_full(test_port=test_port)
        self.move_to_final(interactive)
        self.start_server()

        self.print_footer()


    def print_header(self):
        """Start the output with some informative header"""
        sys.stdout.write("\n")
        sys.stdout.write("*"*50 + "\n")
        sys.stdout.write("*\n")
        sys.stdout.write("* Upgrade KA Lite!\n")
        sys.stdout.write("*\n")
        sys.stdout.write("*\tCurrent install directory: %s\n" % self.current_dir)


    def get_dest_dir(self, zip_name, interactive=True):
        """Prompt for a destination, providing some easy options"""

        neighbor_dir = os.path.realpath(self.current_dir + "/../" + zip_name)

        if interactive:
            sys.stdout.write("*\n")
            sys.stdout.write("* Where would you like to install your KA Lite ugrade to?\n")
            sys.stdout.write("*\t0 : replace the current installation (%s)\n" % self.current_dir)
            sys.stdout.write("*\t1 : %s\n" % self.neighbor_dir)
            sys.stdout.write("*\tOr any other path\n")
            sys.stdout.write("*\n")

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

        sys.stdout.write("*\n")
        sys.stdout.write("* temp location == %s\n" % self.working_dir)
        sys.stdout.write("* Extracting all files to a temporary location; please wait...")
        sys.stdout.flush()

        # Speedup debug by not extracting when path exists and it's not empty.
        #   Works because we don't use a randomly generated temp name in debug mode.
        if settings.DEBUG and os.path.exists(self.working_dir + "/install.sh"):
            sys.stdout.write("** NOTE ** NOT EXTRACTING IN DEBUG MODE")
            return

        if not os.path.exists(self.working_dir):
            os.mkdir(self.working_dir)

        if not zipfile.is_zipfile(zip_file):
            raise CommandError("bad zip file")

        zip = ZipFile(zip_file, "r")

        nfiles = len(zip.namelist())
        for fi,afile in enumerate(zip.namelist()):

            if fi>0 and fi%round(nfiles/10)==0:
                pct_done = round(100.*(fi+1.)/nfiles)
                sys.stdout.write(" %d%%" % pct_done)

            zip.extract(afile, path=self.working_dir)
            # If it's a unix script, give permissions to execute
            if os.path.splitext(afile)[1] == ".sh":
                os.chmod(os.path.realpath(self.working_dir + "/" + afile), 0755)
                settings.LOG.debug("\tChanging perms on script %s\n" % os.path.realpath(self.working_dir + "/" + afile))
        sys.stdout.write("\n")

        # Error checking (successful unpacking would skip all the following logic.)
        if not os.path.exists(self.working_dir + "/kalite/"):
            subdirs = os.listdir(self.working_dir)

            if len(subdirs) == 1:
                # This happens if zip was downloaded from git, rather than being created through the zip_kalite command.
                self.working_dir += "/" + subdirs[0] + "/"
                sys.stdout.write("Note: found a git-based package.  Updating working dir to %s\n" % self.working_dir)

            else:
                # Unexpected situation: no kalite dir, and more than one directory.  What could it be?
                raise CommandError("Expected %s to exist, but it doesn't.  Unknown failure in extraction; exiting." % (self.working_dir + "/kalite/"))


    def copy_in_data(self):
        """Copy over sqlite3 database, then run syncdb"""

        if settings.DATABASES['default']['ENGINE'] != 'django.db.backends.sqlite3':
            sys.stdout.write("Nothing to do for non-sqlite3 database.\n")
            return
        elif not os.path.exists(settings.DATABASES['default']['NAME']):
            sys.stdout.write("KA Lite not yet installed; no data to copy.\n")
            return
        else:
            # Copy over data for sqlite
            sys.stdout.write("* Copying over database to the server update location\n")
            shutil.copy(settings.DATABASES['default']['NAME'], os.path.realpath(self.working_dir + "/kalite/database/data.sqlite"))

        # Run the syncdb
        sys.stdout.write("* Syncing database...")
        out = call_outside_command_with_output(self.working_dir, "migrate")
        out = call_outside_command_with_output(self.working_dir, "syncdb", migrate=True)
        sys.stdout.write("\n")


    def update_local_settings(self):
        """Combine the old and new local settings (put new last, so that they have precedence)"""

        sys.stdout.write("* Updating local settings\n")

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

        # Create combination: package local_settings override current local_settings
        fh = open(self.working_dir + "/kalite/local_settings.py", "w")
        fh.write(cur_ls + "\n" + new_ls)
        fh.close()


    def move_video_files(self):
        """If necessary (determined previously), move video files on disk.
        Otherwise, write into local_settings."""

        # Move over videos
        if self.move_videos == "y":
            if os.path.exists(settings.CONTENT_ROOT):
                video_files = set(glob.glob(settings.CONTENT_ROOT + '*')) - set((settings.CONTENT_ROOT + "note.txt",))
            else:
                video_files = set()
            sys.stdout.write("* Moving over %d files (videos and thumbnails)\n" % len(video_files))
            if not os.path.exists(self.working_dir + "/content/"):
                os.mkdir(self.working_dir + "/content/")
            for video_file in video_files:
                shutil.move(video_file, self.working_dir + "/content/" + os.path.split(video_file)[1])

        else:  # write (append)
            fh = open(self.working_dir + "/kalite/local_settings.py", "a")
            fh.write("\nCONTENT_ROOT = '%s'\n" % settings.CONTENT_ROOT)
            fh.close()


    def test_server_weak(self):
        sys.stdout.write("* Testing the new server (simple)\n")

        out = call_outside_command_with_output(self.working_dir, "update", "test")
        if "Success!" not in out[0]:
            raise CommandError(out[1] if out[1] else out[0])


    def test_server_full(self, test_port=8008):
        """Stop the old server.  Start the new server."""

        sys.stdout.write("* Testing the new server (full)\n")

        # Stop the old server
        stop_cmd = self.get_shell_script("serverstop*", location=self.current_dir + "/kalite/")
        if stop_cmd:
            try:
                p = subprocess.Popen([stop_cmd], shell=False, cwd=os.path.split(stop_cmd)[0], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out = p.communicate()
                if out[1]:
                    raise CommandError(out[1])
            except Exception as e:
                sys.stdout.write("Warning: failed stopping the old server: %s\n" % e)


        # Start the server to validate
        start_cmd = self.get_shell_script("serverstart*", location=self.working_dir + "/kalite/")
        try:
            p = subprocess.Popen([start_cmd, str(test_port)], shell=False, cwd=os.path.split(start_cmd)[0], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out = p.communicate()
            if out[1]:
                raise CommandError(out[1])
        except Exception as e:
            sys.stdout.write("Warning: failed starting the new server: %s\n" % e)

        # Stop the server
        stop_cmd = self.get_shell_script("serverstop*", location=self.working_dir + "/kalite/")
        if stop_cmd:
            try:
                p = subprocess.Popen([stop_cmd], shell=False, cwd=os.path.split(stop_cmd)[0], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out = p.communicate()
                if out[1]:
                    raise CommandError(out[1])
            except Exception as e:
                sys.stdout.write("Warning: failed stopping the new server: %s\n" % e)


    def move_to_final(self, interactive=True):
        """Confirm the move to the new location"""

        # Double-check if destroying old install
        if self.dest_dir == self.current_dir:
            ans = "" if interactive else "y"
            while ans.lower() not in ["y","n"]:
                ans = raw_input("* Server setup verified; complete by moving to the final destination? [y/n]: ").strip()
            if ans=="n":
                sys.stdout.write("**** Aborting update; new server (with content) can be found at %s\n" % self.working_dir)
                exit()

        # OK, don't actually kill it--just move it
        if os.path.exists(self.dest_dir):
            try:
                if platform.system() == "Windows" and self.current_dir == self.dest_dir:
                    # We know this will fail, so rather than get in an intermediate state,
                    #   just move right to the compensatory mechanism.
                    raise Exception("Windows sucks.")

                tempdir = tempfile.mkdtemp()

                sys.stdout.write("* Moving old directory to a temporary location...\n")
                shutil.move(self.dest_dir, tempdir)

                # Move to the final destination
                sys.stdout.write("* Moving new installation to final position.\n")
                shutil.move(self.working_dir, self.dest_dir)

            except Exception as e:
                if str(e) == "Windows sucks.":
                    # We expect this error for Windows (sometimes, see above).
                    sys.stdout.write("Copying contents from temp directory to original directory.\n")
                else:

                    # If the move above fails, then we are in trouble.
                    #   The only way to try and save our asses is to
                    #   move each file from the new installation to the dest location,
                    #   one by one.
                    sys.stdout.write("***** Warning: failed to move: %s to %s:\n" % (self.dest_dir, tempdir))
                    sys.stdout.write("*****        '%s'\n" % e)
                    sys.stdout.write("***** Trying to copy contents into dest_dir\n")

                copy_success = 0  # count the # of files successfully moved over
                for root, dirs, files in os.walk(self.working_dir):
                    # Turn root into a relative path
                    assert root.startswith(self.working_dir), "Root from os.walk should be an absolute path."
                    relpath = root[len(self.working_dir)+1:]

                    # Loop over all directories to create destination directories
                    for d in dirs:
                        drelpath = os.path.join(relpath, d)
                        dabspath = os.path.join(self.dest_dir, drelpath)
                        if not os.path.exists(dabspath):
                            settings.LOG.debug("Created directory %s\n" % (dabspath))
                            os.mkdir(dabspath)

                    # Loop over all files, to move them over.
                    for f in files:
                        try:
                            frelpath = os.path.join(relpath, f)
                            shutil.copyfile(
                                os.path.join(self.working_dir, frelpath),
                                os.path.join(self.dest_dir, frelpath),
                            )
                            copy_success += 1
                        except:
                            sys.stderr.write("**** failed to copy %s\n" % os.path.join(self.working_dir, frelpath))
                sys.stdout.write("* Successfully copied %d files into final directory\n" % copy_success)


    def start_server(self, port=None):
        """
        Start the server, for real (not to test) (cron and web server)
        """

        sys.stdout.write("* Starting the server\n")

        # Start the server to validate
        start_cmd = self.get_shell_script("start*", location=self.current_dir)
        full_cmd = [start_cmd] if not port else [start_cmd, port]
        p = subprocess.Popen(full_cmd, shell=False, cwd=os.path.split(start_cmd)[0], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = p.communicate()
        if out[1]:
            raise CommandError(out[1])

        running_port = out[0].split(" ")[-1]
        sys.stdout.write("* Server accessible @ port %s.\n" % running_port)


    def print_footer(self):
        sys.stdout.write("*\n")
        sys.stdout.write("* Installation complete!\n")
        sys.stdout.write("*"*50 + "\n")

    def kalite_is_installed(self):
        if settings.DATABASES['default']['ENGINE'] != 'django.db.backends.sqlite3':
            return True  # I have no idea, so assume the best.  They updated local_settings and are "sophisticated"

        else:
            return os.path.exists(settings.DATABASES['default']['NAME'])


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
