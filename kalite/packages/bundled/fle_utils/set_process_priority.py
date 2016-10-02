import logging
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

from fle_utils import set_process_priority
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


def _set_windows_priority(priority, logging=logging):
    logging.debug("Cannot set priority, not implemented for Windows")
    return False


def _set_linux_mac_priority(priority, logging=logging):

    try:
        import psutil
    except:
        logging.debug("Cannot set priority, psutil module not installed")
        return False

    this_process = psutil.Process(os.getpid())
    # Psutil is builtin to some python installations, and the versions
    # may differ across devices. It affects the code below, b/c for the 
    # 2.x psutil version. 'this_process.cmdline is a function that 
    # returns a list; in the 1.x version it's just a list. 
    # So we check what kind of cmdline we have, and go from there.
    if isinstance(this_process.cmdline, list):
        cmdline = this_process.cmdline
    else:
        cmdline = this_process.cmdline()
    if "runcherrypyserver" in cmdline:
        logging.debug("Will not set priority, this is the webserver process")
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
        logging.debug("Cannot set priority; probably insufficient privilege")
        return False

    return priority


def _set_priority(priority, logging=logging):

    if SYS_PLATFORM == "Windows":
        return _set_windows_priority(priority, logging=logging)
    elif SYS_PLATFORM in ("Linux", "Mac"):
        return _set_linux_mac_priority(priority, logging=logging)
    else:
        logging.debug("Cannot set priority, Unsupported platform: '%s'" % sysPlatform)
        return False


def low(logging=logging):
    """ Process will execute with lower CPU priority """
    return _set_priority("Low", logging=logging)

def lowest(logging=logging):
    """ Process will only execute when system is idle """
    return _set_priority("Lowest", logging=logging)

def normal(logging=logging):
    """ Process will try to reset to normal priority """
    return _set_priority("Normal", logging=logging)
