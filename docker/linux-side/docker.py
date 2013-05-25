import socket
import subprocess
import time

class Docker(object):
    
    def __init__(self):

        # start the docker, and listen for commands over TCP
        self.p = subprocess.Popen(["docker", "run", "-i", "-t", "-p", "4000", "-p", "5000", "ka-lite-installed", "/bin/bash", "-c", "/pipe.sh"], shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

        # read the ID
        self.ID = self.p.stdout.read(12)

        # read the external port numbers being mapped to the internal ports
        self.PORT_IN = subprocess.Popen(["docker", "port", self.ID, "5000"], shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()[0].strip()
        self.PORT_OUT = subprocess.Popen(["docker", "port", self.ID, "4000"], shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()[0].strip()

        # open a socket to write in commands
        self.s_in = socket.create_connection(("localhost", self.PORT_IN))

        # open a socket to read out responses
        self.s_out = socket.create_connection(("localhost", self.PORT_OUT))
        self.s_out.setblocking(0)

    def run_command(self, input, wait_time=3):
        """ Run a command in the docker via the sockets, delaying before reading the response """
        self.write_stdin(input.strip() + "\n")
        time.sleep(wait_time)
        return self.read_stdout()            
        
    def write_stdin(self, input):
        """ Write commands to the container's shell input """
        self.s_in.send(input.strip() + "\n")
        
    def read_stdout(self, bytes=1000000):
        """ Read from the contents of the response buffer """
        try:
            return self.s_out.recv(bytes)
        except:
            return ""
            
    def checkout_repo_branch(self, owner="learningequality", repo="ka-lite", branch="develop"):
        self.run_command("git clone git://github.com/%s/%s.git" % (owner, repo))
        self.run_command("git checkout %s" % (branch))
        self.run_command("cd %s" % (repo))
        print self.run_command("ls")
    
    def close(self):
        """ Kill the running docker container """
        subprocess.Popen(["docker", "kill", self.ID])

    def __del__(self):
        self.close()


def example():
    d = Docker()
    print d.run_command("cd /ka-lite/kalite")
    print d.run_command("./manage.py syncdb")

