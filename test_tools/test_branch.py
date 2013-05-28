import logging
import os
import socket
import sys

import mount_branch

class SecureSyncEcosystem(object):

    def __init__(self, git_user, repo_branch, git_repo="ka-lite", base_dir="/home/ubuntu/ka-lite", branch_class=mount_branch.KaLiteSnapshotProject):
        self.kp_newbranch = branch_class(git_user=git_user, repo_branch=repo_branch, git_repo=git_repo, base_dir=base_dir)
#        self.kp_master = branch_class(git_user="learningequality", repo_branch="master", git_repo="ka-lite", base_dir=base_dir)
        self.kp_master = branch_class(git_user="learningequality", repo_branch="develop", git_repo="ka-lite", base_dir=base_dir)
        
    def setup_project(self, port_range=(50000, 65000), open_ports=None, port_map=None):
        """set up supporting files.
        Note that for master branch, passed in value 'localx' gets mapped into an actual number
        (e.g. local15)"""
        
        assert open_ports or port_map or port_range
        assert not open_ports or len(open_ports>3)
        assert not port_map or len({"central","local","localx"}.intersect(set(port_map.keys())))==3
        
        self.kp_newbranch.setup_project(server_types=["central", "local"], port_range=port_range, open_ports=open_ports, port_map=port_map)
        
        # Make sure to point master branch to above central server
        if not port_map:
            open_ports = mount_branch.get_open_ports(port_range=port_range, num_ports=1) # system call
            port_map = { "localx": open_ports[0], "central": self.kp_newbranch.servers["central"].port }
            
        # Find the actual path for the master/local branch
        #self.kp_master.setup_project(["localx"], port_range, open_ports, port_map)
        repo_dir = self.kp_master.get_repo_dir('local')
        if not os.path.exists(repo_dir + "/kalite/local_settings.py"):
            self.kp_master.server_key = "local"
        else:
            for i in range(0,100): # never should get this high, otherwise we're using too many resources!
                repo_dir = self.kp_master.get_repo_dir("local%d" % i)
                if not os.path.exists(repo_dir + "/kalite/local_settings.py"):
                    break;
            self.kp_master.server_key = "local%d" % i
        
        # Now set that up. Make sure to point
        port_map[self.kp_master.server_key] = port_map["localx"]
        self.kp_master.setup_project([self.kp_master.server_key], port_map=port_map)
#        unset port_map["localx"]
    
    def mount(self):
        self.kp_newbranch.mount()
        self.kp_master.mount()
        
    def emit_header(self):
        # Emit an informative header
        logging.info("*"*50)
        logging.info("*")
        logging.info("* Setting up %s/%s.git:%s" % (self.kp_newbranch.git_user, self.kp_newbranch.git_repo, self.kp_newbranch.repo_branch))
        logging.info("* \tCentral server path: %s" % self.kp_newbranch.servers["central"].repo_dir)
        logging.info("* \tLocal server path: %s" % self.kp_newbranch.servers["local"].repo_dir)
        logging.info("* \tMASTER server path: %s" % self.kp_master.servers[self.kp_master.server_key].repo_dir)
        logging.info("*")
        logging.info("* \tCentral server URL: http://%s:%d/" % (socket.getfqdn(), self.kp_newbranch.servers["central"].port))
        logging.info("* \tLocal server URL: http://%s:%d/" % (socket.getfqdn(), self.kp_newbranch.servers["local"].port))
        logging.info("* \tMASTER server URL: http://%s:%d/" % (socket.getfqdn(), self.kp_master.servers[self.kp_master.server_key].port))
        logging.info("*")
        logging.info("* Admin info (both servers):")
        logging.info("* \tusername: %s" % self.kp_master.servers[self.kp_master.server_key].admin_user["username"])
        logging.info("* \tpassword: %s" % self.kp_master.servers[self.kp_master.server_key].admin_user["password"])
        logging.info("* \temail: %s"    % self.kp_master.servers[self.kp_master.server_key].admin_user["email"])
        logging.info("*")
        logging.info("*"*50)
        logging.info("")
    
    def mount_project(self, port_range=(50000, 65000), open_ports=None, port_map=None):
        self.setup_project(port_range=(50000, 65000), open_ports=None, port_map=None)
        self.emit_header()
        self.mount()        

    
    def foo(self):
        """Mount branch with one central, one local server.  THEN mount a local server from the  learningequality/master branch.  Add fake data to all three, then test syncing."""
        # Import some data
        for skey,server in kap.servers.items():
            if skey=="central":
                continue;

            # add some data        
            os.chdir(server.repo_dir+"/kalite")
            mount_branch.lexec("python manage.py generatefakedata")
 


def usage(usage_err=None):
    if usage_err:
        logging.info("ERROR: %s" % usage_err)
    
    logging.info("Usage:")
#    logging.info("\t%s <git_username> <git_branch>", sys.argv[0])
    logging.info("\t%s <git_username> <git_branch> [central or local] [port_range (50-60) or port_list(50,51)", sys.argv[0])
#    logging.info("\t%s <git_username> <git_branch> [repository_name]")
    exit()


if __name__=="__main__":
    logging.getLogger().setLevel(logging.INFO)

    # Get command-line args
    git_user     = sys.argv[1]    if len(sys.argv)>1 else usage("Specify a git account")
    repo_branch  = sys.argv[2]    if len(sys.argv)>2 else usage("Specify a repo branch")
    ports        = sys.argv[4]    if len(sys.argv)>4 else "50000-65000"
    git_repo     = sys.argv[5]    if len(sys.argv)>5 else "ka-lite"

    # Parse the server types and ports
    port_arg     = mount_branch.parse_ports(ports)

    # Check/clean up ports
    if not port_arg:
        usage("Could not parse port specification: '%s'" % ports)
    # Gave a list of ports; match them to the list of server types
    if hasattr(port_arg, "open_ports"):
        server_types = ["central","local","localx"]
        port_arg = { "port_map": dict(zip(server_types, port_arg["open_ports"])) }
	
    # Run the project
    sse = SecureSyncEcosystem(git_user=git_user, repo_branch=repo_branch, git_repo=git_repo, base_dir="/home/ubuntu/ka-lite")
    sse.mount_project(**port_arg)
