import os
import platform
import sys
"""
Alters the process CPU and IO priority

Allows Long-running or resource-intensive tasks to have their
priority lowered to maximise web-server response times

Typical usage is for Raspberry Pi background tasks

Requires python-psutil on Linux/Mac

Note: linux/Mac CPU priority cannot be raised again unless you are root

usage:

from utils import set_process_priority
...
set_process_priority.low()
...
set_process_priority.lowest()


"""

#Source Recipes:
#http://code.activestate.com/recipes/496767/
#http://stackoverflow.com/questions/1023038/change-process-priority-in-python-cross-platform
#http://stackoverflow.com/questions/702407/how-to-limit-i-o-consumption-of-python-processes-possibly-using-ionice

sysPlatform = platform.system()  #Linux, Windows, Darwin
if sysPlatform == 'Windows':
    SYS_PLATFORM = "Windows"
elif sysPlatform[0:5] == 'Linux':
    SYS_PLATFORM = 'Linux'
elif sysPlatform == 'Darwin':
    SYS_PLATFORM = 'Mac'
else:
    SYS_PLATFORM = None

    
def _set_windows_priority(priority):
    sys.stdout.write("Cannot set priority, not implemented for Windows\n")
    return False


def _set_linux_mac_priority(priority):        

    try:
        import psutil
    except:
        sys.stdout.write("Cannot set priority, psutil module not installed\n")
        return False
        
    this_process = psutil.Process(os.getpid())
    this_process.cmdline
    if "runcherrypyserver" in this_process.cmdline:
        sys.stdout.write("Will not set priority, this is the webserver process\n")
        return False
            
    # Try here, because priority cannot be raised unless we are root.
    try:
        if priority == "Low":
            this_process.nice = 5
            this_process.set_ionice(psutil.IOPRIO_CLASS_BE)
        elif priority == "Lowest":
            this_process.nice = 19
            this_process.set_ionice(psutil.IOPRIO_CLASS_IDLE)
        elif priority == "Normal":
            this_process.nice = 0
            this_process.set_ionice(psutil.IOPRIO_CLASS_BE)
    except:
        sys.stdout.write("Cannot set priority; probably insufficient privilege\n")  
        return False
        
    return


def _set_priority(priority):

    if SYS_PLATFORM == "Windows":
        return _set_windows_priority(priority)
    elif SYS_PLATFORM in ("Linux", "Mac"):
        return _set_linux_mac_priority(priority)
    else:
        sys.stdout.write("Cannot set priority, Unsupported platform: '%s' \n" % sysPlatform)
        return False
        
            
def low():
    """ Process will execute with lower CPU priority """
    return _set_priority("Low")
def lowest():
    """ Process will only execute when system is idle """
    return _set_priority("Lowest")    
def normal():
    """ Process will try to reset to normal priority """
    return _set_priority("Normal")
    