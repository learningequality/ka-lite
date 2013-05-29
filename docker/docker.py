import logging
import os
import pickle
import re
import socket
import subprocess
import sys
import time


class Docker(object):
    docker_id_length = 12
    
    def __init__(self, image_name, ports_to_open=[]):
        self.port_map = None
        self.s_in = None
        self.s_out = None
        
        [self.port_in, self.port_out, ports_to_open] = self.get_internal_ports(ports_to_open)
        assert self.port_in and self.port_out
        
        self.attach_to_docker(image_name, ports_to_open)
        self.attach_docker_ports(ports_to_open)
        

    def attach_to_docker(self, image_name, ports_to_open):
        # Build the docker command; add all desired open ports        
        docker_cmd  = ["docker", "run", "-i", "-t"]
        for p in ports_to_open:
            docker_cmd += ["-p", str(p)]
        docker_cmd += [image_name, "/bin/bash"]
        docker_cmd += ["-c", """hostname; nc -l %d | /bin/bash 2>&1 | nc -l %d""" % (self.port_in, self.port_out)]
        
        # start the docker, and listen for commands over TCP
        self.p = subprocess.Popen(docker_cmd, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

        # read the ID
        self.ID = self.p.stdout.read(self.__class__.docker_id_length)
        if not re.search(r"^[0-9a-zA-Z]{12}$", self.ID):
            if self.ID[0:6] == "Image ":
                raise Exception("Failed to get docker ID (may be invalid image name (%s); partial error message: %s" % (image_name, self.ID))
            else:
                raise Exception("Failed to get docker ID; partial error message: %s" % self.ID)
            
        logging.debug("Docker ID: %s" % self.ID)
        

    def read_docker_ports(self, ports_to_open):
        # read the external port numbers being mapped to the internal ports
        if not self.port_map:
            self.port_map = dict()
            for p in ports_to_open:
                self.port_map[p] = int(subprocess.Popen(["docker", "port", self.ID, str(p)], shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()[0].strip())
                logging.debug("Mapped docker internal port %d to external port %d" % (p, self.port_map[p]))


    def attach_docker_ports(self, ports_to_open):
        self.read_docker_ports(ports_to_open)
        
        # open a socket to write in commands
        self.s_in = socket.create_connection(("localhost", self.port_map[self.port_in]))

        # open a socket to read out responses
        self.s_out = socket.create_connection(("localhost",  self.port_map[self.port_out]))
        self.s_out.setblocking(0)


    def get_internal_ports(self, taken_ports = []):
    
        # Dynamically choose port_in and port_out, and add to ports_to_open
        port_in = None
        port_out = None
        for i in range(4000, 65535):
            if i not in taken_ports:
                if not port_in:
                    port_in = i
                    taken_ports += [port_in,]
                elif not port_out:
                    port_out = i
                    taken_ports+= [port_out,]
                    break
        return (port_in,port_out,taken_ports)
        
        
    def run_command(self, cmd, block_for_output=None, wait_time=None):
        """ Run a command in the docker via the sockets, delaying before reading the response """

        if block_for_output is None:
            block_for_output = wait_time is None

        assert not block_for_output or not wait_time, "Either run async or, if blocking, don't specify a wait time"""
        
        self.write_stdin(cmd.strip() + "\n")
        if block_for_output:
            return self.wait_for_read()
        else:
            return self.read_stdout(wait_time=wait_time)
    
    
    def stream_command(self, cmd, wait_time=1, wait_step=0.1, alert_step=5):
        self.run_command(cmd=cmd, block_for_output=False, wait_time=0)
        return self.stream_stdout(wait_time=wait_time, wait_step=wait_step)
        
       
    def stream_stdout(self, wait_time=1, wait_step=0.1, alert_step=5):
        all_out = ""
        wait_steps = int(round(wait_time/wait_step))
        alert_every = int(round(alert_step/wait_step))
        
        try:
            for i in range(wait_steps):
                strout = self.read_stdout(wait_time=wait_step).strip()
                print strout,
                sys.stdout.flush()
                all_out += strout
                # alert user every 10s of progress
                if i>0 and i%alert_every == 0:
                    print "[%ds of %ds elapsed]" % (int(i*wait_step),wait_time),
                    sys.stdout.flush()
                
        except Exception as e:
            self.close()
            raise e     
        return all_out   
            
    def write_stdin(self, input):
        """ Write commands to the container's shell input """
        try:
            self.s_in.send(input.strip() + "\n")
        except Exception as e:
            self.close()
            raise e
                
    def read_stdout(self, bytes=1000000, wait_time=0):
        """ Read from the contents of the response buffer """
        try:
            time.sleep(wait_time)
            return self.s_out.recv(bytes)
        except Exception as e:
            if getattr(e, 'errno', None)==11 and getattr(e, 'strerror', None)=="Resource temporarily unavailable":
                return ""
            else:
                self.close()
                raise e

    def wait_for_read(self, wait_step=0.1, wait_time=100):
        """Wait for output; return when no new output comes"""

        strout = ""
        
        for i in range(int(round(wait_time/wait_step))):
            new_out = self.read_stdout(wait_time=0.1)
            if not strout:
                strout = new_out
            elif new_out:
                strout += new_out
            else:
                break;
        
        return strout
    
    def close(self):
        """ Kill the running docker container """

        if self.s_in:
            self.s_in.close()
            self.s_in = None

        if self.s_out:
            self.s_out.close()
            self.s_out = None

        if self.p:
            self.p = None
            # subprocess may have already been unloaded, so re-import inline to be safe.
            # safest way is to call close before __del__ 
            import subprocess 
            subprocess.Popen(["docker", "kill", self.ID]).communicate()
    
            
            
    def __del__(self):
        self.close()


class PersistentDocker(Docker):
    """This class is like docker, but rather than creating and destroying a docker container
    every time, it leaves them to persist and attaches to them, only creating when necessary
    and destroying when requested.
    
    I thought this would let the external port mappings persist; alas, it does not.  Of course not...
    
    It is slightly more efficient, than creating a new docker all over the place.  That is all."""

    pkl_file = os.path.realpath(__file__ + "/../docker_map.pkl")
    docker_dict = None
    
    @classmethod
    def load_docker_dict(cls):
        if not cls.docker_dict:
            if os.path.exists(cls.pkl_file):
                logging.debug("Loaded docker dict from %s" % cls.pkl_file)
                fh = open(cls.pkl_file,"r")
                cls.docker_dict = pickle.load(fh)
                fh.close()
            else:
                logging.debug("Initialized empty docker dict.")
                cls.docker_dict = dict()
    
    @classmethod
    def save_docker_dict(cls):
        logging.debug("Saving docker dict to %s" % cls.pkl_file)
        fh = open(cls.pkl_file, "w")
        pickle.dump(cls.docker_dict, fh)
        fh.close()
        
    @classmethod
    def get_docker_id(cls, container_name, image_name):
        cls.load_docker_dict()
        if image_name in cls.docker_dict.keys() and container_name in cls.docker_dict[image_name].keys():
            return cls.docker_dict[image_name][container_name]
        else:
            return None
            
    @classmethod
    def set_docker_id(cls, docker_id, container_name, image_name):
        cls.load_docker_dict()
        if not image_name in cls.docker_dict.keys():
            cls.docker_dict[image_name] = dict()
        cls.docker_dict[image_name][container_name] = docker_id
        
        cls.save_docker_dict()
        
        
    def __init__(self, container_name, image_name, ports_to_open=[]):
        self.port_map = None
        self.s_in = None
        self.s_out = None
        
        self.container_name = container_name
        self.image_name = image_name

        [self.port_in, self.port_out, ports_to_open] = self.get_internal_ports(ports_to_open)
        assert self.port_in and self.port_out

        self.ID = self.__class__.get_docker_id(container_name, image_name)
        logging.debug("Docker ID: %s" % self.ID)
        
        self.attach_to_docker(image_name, ports_to_open)
        self.__class__.set_docker_id(self.ID, container_name, image_name)
        self.read_docker_ports(ports_to_open)
        


    def attach_to_docker(self, image_name, ports_to_open):
        if not self.ID:
            super(PersistentDocker,self).attach_to_docker(image_name, ports_to_open)
            
        else:
            # Build the docker command; add all desired open ports        
            docker_cmd  = ["docker", "restart", self.ID]
            p = subprocess.Popen(docker_cmd, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            p.communicate()
        
            docker_cmd = ["docker", "attach", self.ID]
        
            # start the docker, and listen for commands over TCP
            self.p = subprocess.Popen(docker_cmd, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

        self.attach_docker_ports(ports_to_open)


    def __del__(self):
        """ Don't kill the docker"""
        
        if self.s_in:
            self.s_in.close()
            self.s_in = None
        if self.s_out:
            self.s_out.close()
            self.s_out = None
        
        
if __name__=="__main__":

    logging.getLogger().level = logging.DEBUG

    ka_internal_port = 8024

    # Non-persistent docker
    if False:
    
        d = Docker("ka-lite-installed", ports_to_open=[ka_internal_port])
        print "Port map: ", d.port_map
    
        print d.run_command("cd /ka-lite/kalite", wait_time=0.1) # commands with no output must wait
    #    print d.run_command("ls -l")
        print d.run_command("python manage.py syncdb --migrate") # commands with output can wait for time or for output to stop
    #    print d.stream_command("python manage.py runserver %d" % ka_internal_port, wait_time=10)
    
        d.close()
    
        # Persistent docker
    else:
        d = PersistentDocker(container_name="foo", image_name="ka-lite-installed", ports_to_open=[ka_internal_port])
        print "Port map: ", d.port_map
    
        print d.run_command("cd /ka-lite/kalite", wait_time=0.1) # commands with no output must wait
        print d.stream_command("python manage.py syncdb --migrate", wait_time=11) # commands with output can wait for time or for output to stop
    
        #d.close()
    