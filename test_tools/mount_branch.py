import logging
import os
import pickle
import shutil
import socket
import sys
import subprocess
import urllib
from zipfile import ZipFile

import playground
from playground.docker.docker import Docker, PersistentDocker
from playground.utils.testing import lexec, get_open_ports


class KaLiteServer(object):
    """Basic object encapuslating our server:
    * can install itself
    * can create its own local_settings file based on object settings
    * can start itself (via cherrypy)
    """
    
    admin_user = { 
        "username": "admin", 
        "email": "admin@example.com", 
        "password": "pass",
    }
    _pyexec = None
    lexec = None
    
    def __init__(self, base_dir, server_type, port, hostname="localhost", central_server_port=None, central_server_host=None):
        self.log = logging.getLogger("kalite")
        self.base_dir = os.path.realpath(base_dir) # make into absolute path
        self.server_type = server_type
        self.port = port
        self.hostname = hostname
        
        self.central_server_host = central_server_host if central_server_host else hostname
        self.central_server_port = central_server_port if central_server_port else port
        
        self.admin_user = self.__class__.admin_user
        
    def start_server(self):
        """By default, run allowing external access."""        
        cwd = os.getcwd()
        os.chdir(self.base_dir + "/kalite")
    
        lexec(self.pyexec() + " manage.py runcherrypyserver host=%s port=%d threads=5 daemonize=true pidfile=%s/kalite/runcherrypyserver.pid" % (self.hostname, self.port, self.base_dir))
    
        os.chdir(cwd)


    def pyexec(self):
        """Return the path to the python executable"""
        
        if not self.__class__._pyexec:   
            (_,pyexec,_) = lexec("bash " + self.base_dir+"/python.sh", silent=True)
            self.__class__._pyexec = pyexec[:-1]
        return self.__class__._pyexec


    def create_local_settings_file(self, local_settings_file=None):
    
        if not local_settings_file:
            local_settings_file = self.base_dir+"/kalite/local_settings.py"
            
        # First, set up localsettings
        self.log.info("Creating local_settings.py @ %s" % local_settings_file)
        local_settings = open(local_settings_file,"w")

        local_settings.write("DEBUG = True\n")
        local_settings.write("TEMPLATE_DEBUG = True\n")

        
    
        if self.server_type=="central":
            local_settings.write("CENTRAL_SERVER = True\n")
            local_settings.write("EMAIL_BACKEND = 'postmark.backends.PostmarkBackend'\n")
            local_settings.write("POSTMARK_API_KEY = 'f0b8e26a-6065-4611-a97d-6af27d89b3a6'\n")
            local_settings.write("CENTRAL_FROM_EMAIL    = 'ben@learningequality.org'\n")
            local_settings.write("CENTRAL_ADMIN_EMAIL   = 'ben@learningequality.org'\n")
            local_settings.write("CENTRAL_CONTACT_EMAIL = 'ben@learningequality.org'\n")

            local_settings.write("CENTRAL_DEPLOYMENT_EMAIL = 'ben@learningequality.org'\n")
            local_settings.write("CENTRAL_SUPPORT_EMAIL    = 'ben@learningequality.org'\n")
            local_settings.write("CENTRAL_DEV_EMAIL        = 'ben@learningequality.org'\n")
            local_settings.write("CENTRAL_INFO_EMAIL       = 'ben@learningequality.org'\n")

            # These should disappear
            local_settings.write("CENTRAL_SERVER_DOMAIN = '%s:%d'\n" % (self.hostname, self.port))
            local_settings.write("CENTRAL_SERVER_HOST = '%s:%d'\n" % (self.hostname, self.port))
        else:
            local_settings.write("CENTRAL_SERVER_DOMAIN = '%s:%d'\n" % (self.central_server_host, self.central_server_port))
            local_settings.write("CENTRAL_SERVER_HOST = '%s:%d'\n" % (self.central_server_host, self.central_server_port))
            local_settings.write("SECURESYNC_PROTOCOL = 'http'\n")
    
        local_settings.close()


    def call_command(self, command, params_string="", input=None):
        """Poor man's version of call_command"""
        
        cwd = os.getcwd()
        os.chdir(self.base_dir + "/kalite")
        
        cmd = self.pyexec() + " manage.py " + command + (" " + params_string if params_string else "")
        self.log.debug("Running '%s'" % cmd)
        out = lexec(cmd, input=input)
        
        os.chdir(cwd)

        return {
            "stdout": out[1],
            "stderr": out[2],
            "exit_code": out[0],
        }
        

    def shell_plus(self, commands):

        if hasattr(commands,"isupper"):
            commands = [commands]

        # Run shell plus
        out = self.call_command("shell_plus", "--quiet-load", input=str.join("\n", commands))
        
        # Parse the output cleanly, in the case where we succeed, for easier manipulation
        if not out['exit_code']:
            cmdout = out['stdout'].replace("\x1b[?1034h","").split("\n>>> ")
            if len(cmdout)>1 and not cmdout[-1]: # markers of successful parse
                 return {
                    'stdout': str.join("\n", cmdout[1:-1]),
                    'stderr': None,
                    'exit_code': 0,
                }
        return out        
    

    def install_server(self):
        # Then, make sure to run the installation
        self.log.info("Creating the database and admin user")
        if os.path.exists(self.base_dir + '/kalite/database/data.sqlite'):
            os.remove(self.base_dir + '/kalite/database/data.sqlite')

        # TODO(bcipolli) 
        # we should check these status codes
        self.call_command("syncdb", "--migrate", input="no\n")
        self.call_command("shell", input="from django.contrib.auth.models import User; User.objects.create_superuser('%s', '%s', '%s')" % (self.admin_user["username"], self.admin_user["email"], self.admin_user["password"]))

        zone_json = self.base_dir + "/kalite/static/data/zone_data.json"
        if os.path.exists(zone_json):
            self.call_command("initdevice '%s' 'central_server_port=%d' %s" % (self.server_type, self.central_server_port, zone_json))
        else:
            self.call_command("initdevice '%s' 'central_server_port=%d'" % (self.server_type, self.central_server_port))
    
    
    def update_server(self, file=None):
        if file:
            self.call_command("update", "--file='%s'" % file)
        else:
            self.call_command("update")
        
        
    def is_installed(self):
        if not os.path.exists(self.base_dir + '/kalite/database/data.sqlite'):
            return False
        else:
            try:
                self.call_command("syncdb", "--migrate", input="no\n")
                return True
            except:
                return False
                
    def setup_server(self):
        # Always destroy/rewrite the local settings
        self.create_local_settings_file()
        self.install_server()

    

class KaLiteProject(object):
    """Encapsulates a basic KA Lite project, with multiple servers (of any configuration)"""

    def __init__(self, base_dir, persistent_ports=True):
        self.base_dir = os.path.realpath(base_dir) # make into an absolute path
        self.persistent_ports = persistent_ports
        self.log = logging.getLogger("kalite")
        
    def get_base_dir(self, server_type):
        return "%s/%s" % (self.base_dir, server_type)
    

    def complete_port_map(self, port_keys, port_range=(50000, 65000), open_ports=None, port_map=None):
        assert port_range or open_ports or port_map, "Must pass either port_range or ports"
    
        if not port_map:
            port_map = dict()

        # Build/complete the port map
        missing_keys = set(port_keys) - set(port_map.keys())
        if missing_keys:
            # Grab ports from open ports, which can be defined, or come from a port range.
            if not open_ports:
                open_ports = get_open_ports(port_range=port_range, num_ports=len(missing_keys)) # system call
            
            for pk in missing_keys:   
                # Get the key from our persistent dict     
                p = self.__class__.get_ports_from_map([self.port_map_key(pk),]) if self.persistent_ports else None
                # If not found, pop it off the open ports list
                port_map[pk] = p[0] if (p and p[0]) else open_ports.pop()
                
            # Save results to our persistent dict
            if self.persistent_ports:
                self.__class__.set_ports_to_map(dict(zip([self.port_map_key(pk) for pk in port_map.keys()], port_map.values())))
                self.__class__.save_port_map()

        return port_map
        

    def setup_project(self, server_types, host="localhost", port_range=(50000, 65000), open_ports=None, port_map=None):
        """ """
        
        # get ports as a numeric list
        port_keys = set(server_types).union({"central"}) # must have a central server port
        port_map = self.complete_port_map(port_keys=port_keys, port_range=port_range, open_ports=open_ports, port_map=port_map)   
        
        # Setting up these servers, but they don't actually exist!
        # ... until we create them, that is! :D 
        self.servers = {}
        for server_type in server_types:
            self.servers[server_type] = KaLiteServer(base_dir=self.get_base_dir(server_type), 
                                                     server_type=server_type, 
                                                     port=port_map[server_type], 
                                                     hostname=host,
                                                     central_server_port=port_map["central"],
                                                     central_server_host=host)
        self.port_map = port_map


    def mount_project(self, *args, **kwargs):
        """Convenience function to set up the project, then to mount it."""
        self.setup_project(*args, **kwargs)
        self.emit_header()
        self.mount()
        
 
    def emit_header(self):
        # Emit an informative header
        self.log.info("*"*50)
        self.log.info("*")
        for key,server in self.servers.items():
            self.log.info("* \t%s server path: %s" % (key, server.base_dir))
        self.log.info("*")
        for key,server in self.servers.items():
            self.log.info("* \t%s server URL: http://%s:%d/" % (key, server.hostname, server.port))
        self.log.info("*")
        self.log.info("* Admin info (both servers):")
        self.log.info("* \tusername: %s" % self.servers[self.servers.keys()[0]].admin_user["username"])
        self.log.info("* \tpassword: %s" % self.servers[self.servers.keys()[0]].admin_user["password"])
        self.log.info("* \temail: %s"    % self.servers[self.servers.keys()[0]].admin_user["email"])
        self.log.info("*")
        self.log.info("*"*50)
        self.log.info("")
        
        
    def port_map_key(self, server_type):
        return "%s/%s" % (self.base_dir, server_type)

    ## variables and class methods for persisting associations
    ## between KA Lite projects and particular ports
    port_map_file = os.path.dirname(os.path.realpath(__file__)) + "/port_map.pkl"
    port_map = None
    
    @classmethod
    def load_port_map(cls, port_map_file=None):
        if not port_map_file:
            port_map_file = cls.port_map_file
        try:
            fp = open(port_map_file, 'r')
            cls.port_map = pickle.load(fp)
            fp.close()
        except Exception as e:
            raise e
        return cls.port_map
    
    @classmethod
    def save_port_map(cls, port_map_file=None):
        if not port_map_file:
            port_map_file = cls.port_map_file 
        try:
            fp = open(port_map_file, 'w')
            pickle.dump(cls.port_map, fp)
            fp.close()
        except Exception as e:
            self.log.warn("Failed to save port map: %s" % e.message)

    @classmethod
    def get_ports_from_map(cls, port_keys):
        if not cls.port_map:
            if os.path.exists(cls.port_map_file):
                cls.port_map = cls.load_port_map(cls.port_map_file)
            else:
                cls.port_map = dict()
        return [cls.port_map[pk] if pk in cls.port_map.keys() else None for pk in port_keys]
        
    @classmethod
    def set_ports_to_map(cls, port_map):
        if not cls.port_map:
            if os.path.exists(cls.port_map_file):
                cls.port_map = cls.load_port_map(cls.port_map_file)
            else:
                cls.port_map = dict()
        cls.port_map = dict(cls.port_map.items() + port_map.items())
    
    


class KaLiteSelfZipProject(KaLiteProject):
    """Encapsulates a KA Lite project, running from a zip generated from KA Lite's "package" function"""
    
    def __init__(self, zip_file, *args, **kwargs):
        super(KaLiteSelfZipProject, self).__init__(*args, **kwargs)
        self.zip_file = zip_file

    def unpack_zip(self, server, force_create=True):
        
        """Set up the specified user's repo as a snapshot--no git history.
        Return the directory it's set up in!"""
    
        self.log.debug("Setting up %s" % (self.zip_file))
    
        # Create the branch directory
        if os.path.exists(self.base_dir):
            self.log.info("Mounting KA Lite project to an existing dir: %s" % self.base_dir)
        else:
            self.log.info("Creating new project dir: %s" % self.base_dir)
            
        if os.path.exists(server.base_dir):
            self.log.info("Removing server base_dir: %s" % server.base_dir)
            shutil.rmtree(server.base_dir)
        self.log.info("Creating server base dir: %s" % server.base_dir)
        os.makedirs(server.base_dir)

        self.log.info("Unpacking self-packed zip to %s" % server.base_dir)
        ZipFile(self.zip_file).extractall(server.base_dir)

    
    def mount(self):

        # Set up central and local servers, in turn
        #
        # Do this through numeric iteration, so that we
        #   are guaranteed to move the snapshot on the last iteration, 
        #   which is important to save disk space
        #
        for key,server in self.servers.items():
            if not server.is_installed():
                self.unpack_zip(server)
                server.setup_server()
            else:
                server.update_server(file=self.zip_file)
            server.start_server()
                

class KaLiteGitProject(KaLiteProject):
    """Encapsulates a KA Lite project, running through a git repository"""
    
    def __init__(self, git_user, repo_branch, git_repo="ka-lite", base_dir=os.path.dirname(os.path.realpath(__file__))):
        super(KaLiteGitProject, self).__init__(base_dir)
        
        self.git_user = git_user
        self.repo_branch = repo_branch
        self.git_repo = git_repo

        self.user_dir   = self.base_dir + "/" + self.git_user
        self.branch_dir = self.user_dir + "/" + self.repo_branch


    def get_base_dir(self, server_type):
        return self.get_repo_dir(server_type)
        
    def get_repo_dir(self, server_type):
        return self.branch_dir+"/"+server_type
                                                             
    def setup_project(self, *args, **kwargs):#server_types, port_range=(50000, 65000), open_ports=None, port_map=None):
        """Sets up the branch directories, points to a directory for local and central"""
    
        # Create the branch directory
        if os.path.exists(self.branch_dir):
            self.log.debug("Using branch directory: %s" % self.branch_dir)
        else:
            self.log.debug("Creating branch directory: %s" % self.branch_dir)
            os.makedirs(self.branch_dir)
            
        super(KaLiteGitProject, self).setup_project(*args, **kwargs)
        #server_types, port_range, open_ports, port_map)
            
                
    def port_map_key(self, server_type):
        return "%s/%s.git:%s %s" % (self.git_user, self.git_repo, self.repo_branch, server_type)

    def emit_header(self):
        # Emit an informative header
        self.log.info("*"*50)
        self.log.info("*")
        self.log.info("* Setting up %s/%s.git:%s" % (self.git_user, self.git_repo, self.repo_branch))
        for key,server in self.servers.items():
            self.log.info("* \t%s server path: %s" % (key, server.base_dir))
        self.log.info("*")
        for key,server in self.servers.items():
            self.log.info("* \t%s server URL: http://%s:%d/" % (key, server.hostname, server.port))
        self.log.info("*")
        self.log.info("* Admin info (both servers):")
        self.log.info("* \tusername: %s" % self.servers[self.servers.keys()[0]].admin_user["username"])
        self.log.info("* \tpassword: %s" % self.servers[self.servers.keys()[0]].admin_user["password"])
        self.log.info("* \temail: %s"    % self.servers[self.servers.keys()[0]].admin_user["email"])
        self.log.info("*")
        self.log.info("*"*50)
        self.log.info("")



class KaLiteRepoProject(KaLiteGitProject):
    """Encapsulates a KA Lite project, running through a live git repository"""
    
    def setup_repo(self, server):
        """Set up the specified user's repo as a remote; return the directory it's set up in!"""
    
        if self.git_repo != "ka-lite":
            raise NotImplementedError("Only ka-lite repo has been implemented!")
        
        self.log.debug("Setting up %s %s %s" % (self.git_user, self.repo_branch, self.git_repo))
    
        # Create the branch directory
        self.branch_dir = os.path.realpath(server.base_dir + "/..")
        if os.path.exists(self.branch_dir):
            self.log.info("Mounting git to existing branch dir: %s" % self.branch_dir)
        else:
            self.log.info("Creating branch dir")
            os.makedirs(self.branch_dir)


        # clone the git repository
        os.chdir(self.branch_dir)
        # Directory exists, maybe it's already set up? 
        if os.path.exists(server.base_dir):
            os.chdir(server.base_dir)
            (_,stdout,stderr) = lexec("git remote -v")
            # It contains the desired repo; good enough. 
            # TODO(bcipolli): really should check if the repo is ORIGIN
            if -1 != stdout.find("%s/%s.git" % (self.git_user, self.git_repo)):
                self.log.warn("Not touching existing git repository @ %s" % self.repo_dir)
                return server.base_dir
    #        else:
    #            raise Exception(stderr)
            os.chdir(self.branch_dir) # return to branch dir
        
        self.log.info("Cloning %s/%s.git to %s" % (self.git_user, self.git_repo, server.base_dir))
        lexec("git clone git@github.com:%s/%s.git %s" % (self.git_user, self.git_repo, os.path.basename(server.base_dir)))


            
    def select_branch(self, server):
        if server.base_dir:
            cwd = os.getcwd()
            os.chdir(server.base_dir)
    
        # Get the current list of branches
        lexec("git fetch")
    
        # List the branches
        (_,stdout,_) = lexec("git branch")
    
        # Branch doesn't exist; create it
        if -1 == stdout.find("%s\n" % self.repo_branch): # note: this is a CRAPPY match!
            self.log.info("Connecting to branch %s" % self.repo_branch)
            lexec("git checkout -t origin/%s" % self.repo_branch)
        else:
            self.log.info("Changing to branch %s" % self.repo_branch)
            lexec("git checkout %s" % self.repo_branch)
            lexec("git pull origin %s" % self.repo_branch)
        
        # switch directory back
        if repo_dir:
            os.chdir(cwd)
        
        
    def mount(self):

        # Set up central and local servers, in turn
        for key,server in self.servers.items():
            if not server.is_installed():
                self.setup_repo(server)
                self.select_branch(server)
                server.setup_server()
            else:
                server.update_server()
            server.start_server()



class KaLiteGitSnapshotProject(KaLiteGitProject):
    """Encapsulates a KA Lite project, using a snapshot of a git repository,
    downloaded from the git website."""
    
    def __init__(self, *args, **kwargs):
        super(KaLiteGitSnapshotProject, self).__init__(*args, **kwargs)

        self.snapshot_url  = "https://github.com/%s/%s/archive/%s.zip" % (self.git_user, self.git_repo, self.repo_branch)
        self.snapshot_file = self.branch_dir + "/%s.zip" % self.repo_branch
        self.snapshot_dir  = self.branch_dir + "/%s-%s" % (self.git_repo, self.repo_branch)


    def setup_repo_snapshot(self, server, force_create=False, move_snapshot=False):
        """Set up the specified user's repo as a snapshot--no git history.
        Return the directory it's set up in!"""
    
        if self.git_repo != "ka-lite":
            raise NotImplementedError("Only ka-lite repo has been implemented (repo=%s specified)!" % self.git_repo)
        
        self.log.debug("Setting up %s %s %s" % (self.git_user, self.repo_branch, self.git_repo))
    
        # Create the branch directory
        if os.path.exists(self.branch_dir):
            self.log.info("Mounting git to existing branch dir: %s" % self.branch_dir)
        else:
            self.log.info("Creating branch dir")
            os.makedirs(self.branch_dir)


        os.chdir(self.branch_dir)
    
        # Create a snapshot if we haven't before
        if not self.snapshot_dir:
            force_create = True

        # Need to take a new snapshot
        if os.path.exists(self.snapshot_dir) and force_create:
            shutil.rmtree(self.snapshot_dir)

        # Create the snapshot        
        if os.path.exists(self.snapshot_dir):
            self.log.info("Using existing snapshot: %s" % self.snapshot_dir)
        else:
            self.log.info("Downloading repo snapshot to %s from %s" % (self.snapshot_file, self.snapshot_url))
            urllib.urlretrieve(self.snapshot_url, self.snapshot_file)
    
            self.log.info("Unpacking snapshot to %s" % self.snapshot_dir)
            ZipFile(self.snapshot_file).extractall(self.branch_dir)

            # remove zip file
            os.remove(self.snapshot_file)
            
        # Always redo the server.
        if os.path.exists(server.base_dir):# and force_create:
            self.log.info("Removing old snapshot directory: %s" % server.base_dir)
            shutil.rmtree(server.base_dir)

        # Now use the snapshot to create the server directory
#        if os.path.exists(server.base_dir):
#            self.log.info("Leaving existing repo: %s" % server.base_dir)
#        else:
        if move_snapshot:
            self.log.info("Moving snapshot to %s" % server.base_dir)
            shutil.move(self.snapshot_dir, server.base_dir)
        else:
            self.log.info("Copying snapshot to %s" % server.base_dir)
            shutil.copytree(self.snapshot_dir, server.base_dir)

    
    def mount(self):

        # Set up central and local servers, in turn
        #
        # Do this through numeric iteration, so that we
        #   are guaranteed to move the snapshot on the last iteration, 
        #   which is important to save disk space
        #
        nkeys = len(self.servers.keys())
        for i in range(nkeys):#key,server in self.servers.items():
            key = self.servers.keys()[i]
            server = self.servers[key]
            
            if not server.is_installed():
                self.setup_repo_snapshot(server, move_snapshot=(i==nkeys-1))
                server.setup_server()
            else:
                # Need to get a zip file
                if not os.path.exists(self.snapshot_file):
                    self.log.info("Downloading repo snapshot to %s from %s" % (self.snapshot_file, self.snapshot_url))
                    urllib.urlretrieve(self.snapshot_url, self.snapshot_file)
                server.update_server(file=self.snapshot_file)
            server.start_server()
            
        # Could remove snapshot file & dir here


class KaLiteDockerProjectWrapper(KaLiteGitProject):
    """Encapsulates a KA Lite project running on git, but through a docker.
    Calls into the docker to do all the work."""

    def __init__(self, image_name="ka-lite-installed", **kwargs):
        super(KaLiteDockerProjectWrapper, self).__init__(**kwargs)
        
        self.image_name = image_name
        self.docker_port = 8000 # hard-coded for now; could be a parameter somewhere.  But this value doesn't really matter.
            
    def get_repo_dir(self, branch_name):
        assert False
        
    def get_docker_name(self, server_type):
        return self.git_user + "/" + self.git_repo + ".git:" + self.repo_branch + " " + server_type


    def setup_project(self, server_types):
        """Sets up the branch directories, points to a directory for local and central"""
    
        assert hasattr(server_types, "pop"), "Server_types must be a list."

        # Create dockers        
        self.dockers = {}
        for server_type in server_types:
            self.log.debug("Creating docker for server_type=%s" % server_type)
#            self.dockers[server_type] = Docker(image_name=self.image_name, ports_to_open=[self.docker_port,])
            self.dockers[server_type] = PersistentDocker(container_name=self.get_docker_name(server_type), image_name=self.image_name, ports_to_open=[self.docker_port,])
            self.dockers[server_type].run_command("cd /playground", wait_time=0.1)
            self.dockers[server_type].stream_command("git pull", wait_time=3)


    def mount(self, wait_time=90):
        for server_type,docker in self.dockers.items():
            docker.run_command("export PYTHONPATH=${PYTHONPATH}:/playground", wait_time=0.1)
            docker.stream_command("python /playground/test_tools/mount_branch_on_docker.py %s %s %s %d %s" % (self.git_user, self.repo_branch, server_type, self.docker_port, self.git_repo), wait_time=wait_time)


    def mount_project(self, wait_time=90, *args, **kwargs):
        self.setup_project(self, *args, **kwargs)
        self.emit_header()
        self.mount(wait_time)
            
                
    def emit_header(self):
        # Emit an informative header
        self.log.info("*"*50)
        self.log.info("*")
        self.log.info("* Setting up %s/%s.git:%s" % (self.git_user, self.git_repo, self.repo_branch))
        for key,docker in self.dockers.items():
            self.log.info("* \t%s container ID: %s" % (key, docker.ID))
        self.log.info("*")
        for key,docker in self.dockers.items():
            self.log.info("* \t%s server URL: http://%s:%d/" % (key, socket.getfqdn(), docker.port_map[self.docker_port]))
        self.log.info("*")
#        self.log.info("* Admin info (both servers):")
#        self.log.info("* \tusername: %s" % self.servers[self.servers.keys()[0]].admin_user["username"])
#        self.log.info("* \tpassword: %s" % self.servers[self.servers.keys()[0]].admin_user["password"])
#        self.log.info("* \temail: %s"    % self.servers[self.servers.keys()[0]].admin_user["email"])
#        self.log.info("*")
        self.log.info("*"*50)
        self.log.info("")

    
            
            
    def mount_project(self, server_types):
        """Convenience function to set up the project, then to mount it."""
        self.setup_project(server_types)
        self.emit_header()
        self.mount()
        


class KaLiteDockerRepoProject(KaLiteRepoProject):
    """This is what gets called, once we're in the docker"""
    
    def __init__(self, *args, **kwargs):
        super(KaLiteDockerRepoProject,self).__init__(*args, **kwargs)
        self.user_dir = '/'
        self.base_dir = '/'
        
    def get_repo_dir(self, branch_name):
        return '/ka-lite'
        
    def setup_repo(self, server):
        """Set up the specified user's repo as a remote; return the directory it's set up in!"""
        
        if self.git_repo != "ka-lite":
            raise NotImplementedError("Only ka-lite repo has been implemented!")
    
        self.log.debug("Setting up %s %s %s" % (self.git_user, self.repo_branch, self.git_repo))
    
#        self.docker.run_command("/playground/test_tools/mount_docker_branch.sh %s %s %s" % (self.git_user, self.git_repo, self.repo_branch))
    
        # Add the remote        
        os.chdir(server.base_dir)
    
        self.log.info("Adding remote %s/%s.git to %s" % (self.git_user, self.git_repo, server.base_dir))
        remote_url = "git://github.com/%s/%s.git" % (self.git_user, self.git_repo)
        lexec("git remote add %s %s" % (self.git_user, remote_url));
        if not remote_url in lexec("git remote -v")[1]:
            raise Exception("Failed to add remote to git (%s)" % remote_url)
    
        # Merge in the remote branch
        lexec("git fetch %s" % self.git_user)
        lexec("git merge %s/%s" % (self.git_user, self.repo_branch))
        
        """
        self.docker.run_command("cd %s" % server.base_dir, wait_time=0.1)
        self.log.info("Adding remote %s/%s.git to %s" % (self.git_user, self.git_repo, server.base_dir))
        remote_url = "git://github.com/%s/%s.git" % self.git_user, self.git_repo
        self.docker.run_command("git remote add %s git://github.com/%s/%s.git" % (self.git_user, remote_url) , wait_time=0.5);
        if not remote_url in self.docker.run_command("git remote -v"):
            raise Exception("Failed to add remote to git (%s)" % remote_url)
        
        # Merge in the remote branch
        self.docker.stream_command("git fetch %s" % self.git_user, wait_time=3)
        self.docker.run_command("git merge %s/%s" % (self.git_user, self.repo_branch), wait_time=3)
        """
    
    def mount(self):

        # Set up central and local servers, in turn
        for key,server in self.servers.items():
            self.log.debug("Setting up server %s on docker %s" % (key, "(NYI)"))
            self.setup_repo(server)
            server.setup_server() # must intervene
            server.start_server() # must intervene



def parse_ports(ports):
    """Returns a dict describing the port content"""

    # Port range specified.  
    #  Either get the port from a previous port map, or 
    #  allow the app to randomly choose.
    if -1 != ports.find("-"): # port range
        # default output
        setup_args = { "port_range": map(int,ports.split("-"))}

    # Select specific ports
    elif -1 != ports.find(","): # specific ports
        setup_args = { "open_ports": map(int,ports.split(","))}

    else:
        setup_args = None

    return setup_args


def usage(usage_err=None):
    if usage_err:
       sys.stderr.write("ERROR: %s\n\n" % usage_err)
    
    sys.stderr.write("%s <mount_method [merge,snapshot,docker]> <git_username> <git_branch> [server_type] [port_info]\n" % sys.argv[0])
    sys.stderr.write("\tMounts a KA-Lite git branch at a public URL, using either git merge, dowloading a git snapshot, or mounting within a docker.\n")
    sys.stderr.write("\n")
    sys.stderr.write("Optional args:\n")
    sys.stderr.write("\tserver_type: central or local\n")
    sys.stderr.write("\tport info: a port range (e.g. 50-60) or port list (e.g. 50,51)\n")
    sys.stderr.write("\n")
    sys.exit(1)


if __name__=="__main__":
    logging.getLogger("kalite").setLevel(logging.DEBUG)

    # Get command-line args
    method       = sys.argv[1]    if len(sys.argv)>1 else usage("Specify a mount method")
    git_user     = sys.argv[2]    if len(sys.argv)>2 else usage("Specify a git account")
    repo_branch  = sys.argv[3]    if len(sys.argv)>3 else usage("Specify a repo branch")
    server_types = sys.argv[4]    if len(sys.argv)>4 else "central,local"
    ports        = sys.argv[5]    if len(sys.argv)>5 else "50000-65000"
    git_repo     = sys.argv[6]    if len(sys.argv)>6 else "ka-lite"

    # Parse the server types and ports
    server_types = server_types.split(",")
    port_arg     = parse_ports(ports)

    # Check/clean up ports
    if not port_arg:
        usage("Could not parse port specification: '%s'" % ports)
    # Gave a list of ports; match them to the list of server types
    if hasattr(port_arg, "open_ports"):
        if len(server_types) != len(port_arg["open_ports"]):
            usage("Port list and server type list must have the same length.")
        port_arg = { "port_map": dict(zip(server_types, port_arg["open_ports"])) }


    # Run the project
    if method == "merge":
        kap = KaLiteRepoProject(git_user=git_user, repo_branch=repo_branch, git_repo=git_repo, base_dir="/home/ubuntu/ka-lite")

    elif method == "snapshot":
        kap = KaLiteGitSnapshotProject(git_user=git_user, repo_branch=repo_branch, git_repo=git_repo, base_dir="/home/ubuntu/ka-lite")

    elif method == "docker":
        kap = KaLiteDockerProjectWrapper(git_user=git_user, repo_branch=repo_branch, git_repo=git_repo, image_name="ka-lite-testing")
    else:
        usage("Unknown mount method: '%s'" % method)
        

    kap.mount_project(server_types=server_types, host="playground.learningequality.org")


    # When in debug mode, there's a lot of output--so output again!
    if logging.getLogger().level>=logging.DEBUG:
        kap.emit_header()


    if method == "docker":
        # Don't exit!!
        logging.warning("Dockers STOP after exiting this script.  For now, putting debug HALT so that we can control program exit. :(")
        import pdb; pdb.set_trace()
