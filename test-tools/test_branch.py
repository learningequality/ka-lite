import logging
import os
import sys

import mount_branch



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
    server_types = sys.argv[3]    if len(sys.argv)>3 else "central,local"
    ports        = sys.argv[4]    if len(sys.argv)>4 else "50000-65000"
    git_repo     = sys.argv[5]    if len(sys.argv)>5 else "ka-lite"

    # Parse the server types and ports
    server_types = server_types.split(",")
    port_arg     = mount_branch.parse_ports(ports)

    # Check/clean up ports
    if not port_arg:
        usage("Could not parse port specification: '%s'" % ports)
    # Gave a list of ports; match them to the list of server types
    if hasattr(port_arg, "open_ports"):
        if len(server_types) != len(port_arg["open_ports"]):
            usage("Port list and server type list must have the same length.")
        port_arg = { "port_map": dict(zip(server_types, port_arg["open_ports"])) }
	
    # Run the project
    kap = mount_branch.KaLiteSnapshotProject(git_user=git_user, repo_branch=repo_branch, git_repo=git_repo, base_dir="/home/ubuntu/ka-lite")
    kap.setup_project(server_types=server_types, **port_arg)
    kap.emit_header()
    kap.mount()

    # Import some data
    for skey,server in kap.servers.items():
        if skey=="central":
            continue;

        # add some data        
        os.chdir(server.repo_dir+"/kalite")
        mount_branch.lexec("python manage.py generatefakedata")
 
    # When in debug mode, there's a lot of output--so output again!
    if logging.getLogger().level>=logging.DEBUG:
        kap.emit_header()


