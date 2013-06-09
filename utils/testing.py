import logging
import subprocess

def lexec(cmd, input=None, silent=False):
    """Launch a command"""

    if not silent:
        logging.info("\t%s" % cmd)
    
    cmd = cmd.strip().split(" ") #TODO(bcipolli): do this properly lol

    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (cmd_stdout,cmd_stderr) = p.communicate(input=input)
    if p.returncode:
        if not silent:
            logging.warning("\t\tERROR: return_code=%d, stderr=%s, stdout=%s" % (p.returncode, cmd_stderr, cmd_stdout))
    elif not silent:
        logging.debug("\t\tOutput: %s" % cmd_stdout)
        
    return (p.returncode, cmd_stdout, cmd_stderr)


def get_open_ports(port_range=(50000, 65000), num_ports=1):
    try:
        (_,stdout,_) = lexec("nmap 127.0.0.1 -p%d-%d" % port_range, silent=True)
    except:
        # If nmap doesn't exist, this will fail
        stdout = ""
        
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
    
    return range(port, port+num_ports)
    