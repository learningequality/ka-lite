import logging
import sys

from mount_branch import KaLiteDockerRepoProject(KaLiteRepoProject):


if __name__=="__main__":
    logging.getLogger().setLevel(logging.DEBUG)

    # Get command-line args
    git_user     = sys.argv[1]    if len(sys.argv)>1 else usage("Specify a git account")
    repo_branch  = sys.argv[2]    if len(sys.argv)>2 else usage("Specify a repo branch")
    server_type  = sys.argv[3]    if len(sys.argv)>3 else "local"
    port         = sys.argv[4]    if len(sys.argv)>4 else "8008"
    git_repo     = sys.argv[5]    if len(sys.argv)>5 else "ka-lite"

    # Parse the server types and ports
    port_arg     = int(port)
    
    kap = KaLiteDockerRepoProject(server_type=server_type, git_user=git_user, repo_branch=repo_branch, git_repo=git_repo, )
    kap.mount_project([server_type,], **port_arg)
    
    # When in debug mode, there's a lot of output--so output again!
    if logging.getLogger().level>=logging.DEBUG:
        kap.emit_header()
