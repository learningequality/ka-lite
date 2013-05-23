import logging
import os
import socket
import sys
import subprocess

admin_user = { 
    "username": "admin", 
    "email": "admin@example.com", 
    "password": "pass",
}

def lexec(cmd, input=None, silent=False):
    """Launch a command"""

    if not silent:
        logging.info("\t%s" % cmd)
    
    cmd = cmd.split(" ")

    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (cmd_stdout,cmd_stderr) = p.communicate(input=input)
    if p.returncode:
        if not silent:
            logging.warning("\t\tERROR: %s" % cmd_stderr)
    elif not silent:
        logging.debug("\t\tOutput: %s" % cmd_stdout)
    return (p.returncode, cmd_stdout, cmd_stderr)
    

def start_kalite_server(repo_dir, port):
    """ """
    cwd = os.getcwd()
    os.chdir(repo_dir)
    
    (_,pyexec,_) = lexec("python.sh", silent=True)
    lexec(pyexec[:-1] + " kalite/manage.py runcherrypyserver host=0.0.0.0 port=%d threads=50 daemonize=true pidfile=kalite/runcherrypyserver.pid" % port)
    
    os.chdir(cwd)


def get_open_ports(port_range=(9000, 9999), num_ports=1):
    (_,stdout,_) = lexec("nmap 127.0.0.1 -p%d-%d" % port_range, silent=True)

    #Nmap scan report for localhost.localdomain (127.0.0.1)
    #Host is up (0.00056s latency).
    #Not shown: 999 closed ports
    #PORT     STATE SERVICE
    #9001/tcp open  tor-orport

    #Nmap done: 1 IP address (1 host up) scanned in 0.15 seconds
    import random;
    for i in range(100):
        port = port_range[0] + int(round(random.random()*(port_range[1]-port_range[0]+1)))
        
        # If any port in the sequence is taken, try again... (continue)
        for j in range(num_ports):
            if str(port+j) in stdout:
                continue
                
        # All ports were OK; get out!
        break
    
    return range(port, port+num_ports+1)
    

def setup_kalite_server(repo_dir, server_type, central_server_port=None):
    # Always destroy/rewrite the local settings

    # First, set up localsettings
    logging.info("Creating local_settings.py")
    local_settings = open(repo_dir+"/kalite/local_settings.py","w")

    local_settings.write("DEBUG = True\n")
    local_settings.write("TEMPLATE_DEBUG = True\n")

    hostname = socket.getfqdn()
    
    if server_type=="central":
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
        local_settings.write("CENTRAL_SERVER_DOMAIN = '%s:%d'\n" % (hostname,central_server_port))
        local_settings.write("CENTRAL_SERVER_HOST = '%s:%d'\n" % (hostname,central_server_port))
    else:
        local_settings.write("CENTRAL_SERVER_DOMAIN = '%s:%d'\n" % (hostname,central_server_port))
        local_settings.write("CENTRAL_SERVER_HOST = '%s:%d'\n" % (hostname,central_server_port))
        local_settings.write("SECURESYNC_PROTOCOL = 'http'\n")
    
    local_settings.close()

    # Then, make sure to run the installation
    logging.info("Creating the database and admin user")
    cwd = os.getcwd()
    os.chdir(repo_dir)
    if os.path.exists('kalite/database/data.sqlite'):
        os.remove('kalite/database/data.sqlite')
    lexec('kalite/manage.py syncdb --migrate', input="no\n")
    lexec("kalite/manage.py shell", input="from django.contrib.auth.models import User; User.objects.create_superuser('%s', '%s', '%s')" % (admin_user["username"], admin_user["email"], admin_user["password"]))
    lexec("kalite/manage.py initdevice '%s' 'central_server_port=%d'" % (server_type,central_server_port))
    
    os.chdir(cwd)
    
    
def select_branch(repo_branch, repo_dir=None):
    if repo_dir:
        cwd = os.getcwd()
        os.chdir(repo_dir)
    
    # Get the current list of branches
    lexec("git fetch")
    
    # List the branches
    (_,stdout,_) = lexec("git branch")
    
    # Branch doesn't exist; create it
    if -1 == stdout.find("%s\n" % repo_branch): # note: this is a CRAPPY match!
        logging.info("Connecting to branch %s" % repo_branch)
        lexec("git checkout -t origin/%s" % repo_branch)
    else:
        logging.info("Changing to branch %s" % repo_branch)
        lexec("git checkout %s" % repo_branch)
        lexec("git pull origin %s" % repo_branch)
        
    # switch directory back
    if repo_dir:
        os.chdir(cwd)
        

def setup_repo(git_user, repo_branch, git_repo="ka-lite", repo_dir="."):
    """Set up the specified user's repo as a remote; return the directory it's set up in!"""
    
    if git_repo != "ka-lite":
        raise NotImplementedException("Only ka-lite repo has been implemented!")
        
    logging.debug("Setting up %s %s %s" % (git_user, repo_branch, git_repo))
    
    # Create the branch directory
    branch_dir = os.path.realpath(repo_dir + "/..")
    if os.path.exists(branch_dir):
        logging.info("Mounting git to existing branch dir: %s" % branch_dir)
    else:
        logging.info("Creating branch dir")
        os.makedirs(branch_dir)


    # clone the git repository
    os.chdir(branch_dir)
    # Directory exists, maybe it's already set up? 
    if os.path.exists(repo_dir):
        os.chdir(repo_dir)
        (_,stdout,stderr) = lexec("git remote -v")
        # It contains the desired repo; good enough. 
        # TODO(bcipolli): really should check if the repo is ORIGIN
        if -1 != stdout.find("%s/%s.git" % (git_user, git_repo)):
            logging.warn("Not touching existing git repository @ %s" % repo_dir)
            return repo_dir
#        else:
#            raise Exception(stderr)
        os.chdir(branch_dir) # return to branch dir
        
    logging.info("Cloning %s/%s.git to %s" % (git_user, git_repo, repo_dir))
    lexec("git clone git@github.com:%s/%s.git %s" % (git_user, git_repo, os.path.basename(repo_dir)))

    return repo_dir
    

def setup_project(git_user, repo_branch):
    """Sets up the branch directories, points to a directory for local and central"""
    
    user_dir   = os.path.dirname(os.path.realpath(__file__)) + "/"+git_user
    branch_dir = user_dir +"/"+repo_branch

    # Create the branch directory
    if os.path.exists(branch_dir):
        logging.debug("Using branch directory: %s" % branch_dir)
    else:
        logging.debug("Creating branch directory: %s" % branch_dir)
        os.makedirs(branch_dir)

    return { 
        "local": branch_dir + "/local",
        "central": branch_dir + "/central",
    }
    
    
def usage():
    logging.info("Usage:")
#    logging.info("\t%s <git_username> <git_branch>", sys.argv[0])
    logging.info("\t%s <git_username> <git_branch> [central or local]", sys.argv[0])
#    logging.info("\t%s <git_username> <git_branch> [repository_name]")
    exit()

if __name__=="__main__":
    # Get command-line args
    logging.getLogger().setLevel(logging.INFO)
    git_user    = sys.argv[1]    if len(sys.argv)>1 else usage()
    repo_branch = sys.argv[2]    if len(sys.argv)>2 else usage()
    server_type = [sys.argv[3],] if len(sys.argv)>3 else ["central", "local"]
    git_repo    = sys.argv[4]    if len(sys.argv)>4 else "ka-lite"

    # Get basic variables
    repo_dirs  = setup_project(git_user, repo_branch)
    open_ports = get_open_ports(num_ports=2) 
    ports      = { "central": open_ports[0], "local": open_ports[1] }
    
    # Emit an informative header
    logging.info("*"*50)
    logging.info("* Setting up %s/%s.git:%s" % (git_user, git_repo, repo_branch))
    if "central" in server_type:
        logging.info("* \tCentral server path: %s" % repo_dirs["central"])
    if "local" in server_type:
        logging.info("* \tLocal server path: %s" % repo_dirs["local"])
    logging.info("*")
    if "central" in server_type:
        logging.info("* \tCentral server URL: http://%s:%d/" % (socket.getfqdn(), ports["central"]))
    if "local" in server_type:
        logging.info("* \tLocal server URL: http://%s:%d/" % (socket.getfqdn(), ports["local"]))
    logging.info("*")
    logging.info("* Admin info (both servers):")
    logging.info("* \tusername: %s" % admin_user["username"])
    logging.info("* \tpassword: %s" % admin_user["password"])
    logging.info("* \temail: %s" % admin_user["email"])
    logging.info("*"*50)
    logging.info("")
    
    # Set up central and local servers, in turn
    for key,repo_dir in repo_dirs.items():
        if key not in server_type:
            continue
        setup_repo(git_user, repo_branch, git_repo, repo_dir=repo_dir)
        select_branch(repo_branch, repo_dir=repo_dir)
        setup_kalite_server(repo_dir=repo_dir, server_type=key, central_server_port=ports["central"])
        start_kalite_server(repo_dir=repo_dir, port=ports[key])