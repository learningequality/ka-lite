"""
Alters the process CPU and IO priority

Allows Long-running or resource-intensive tasks to have their
priority lowered to maximise web-server response times

Typical usage is for Raspberry Pi background tasks

Requires python-psutil on Linux/Mac
Requires win32api,win32process and win32con on Windows

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

def _set_priority(priority):

    import platform
    sysPlatform = platform.system()  #Linux, Windows, Darwin
    if sysPlatform == 'Windows':
        SYS_PLATFORM = "Windows"
    elif sysPlatform[0:5] == 'Linux':
        SYS_PLATFORM = 'Linux'
    elif sysPlatform == 'Darwin':
        SYS_PLATFORM = 'Mac'
    else:
        raise Exception("Cannot set priority, Unsupported platform: '%s'" % sysPlatform)

    if SYS_PLATFORM == "Windows":
        try:
            import win32api,win32process,win32con
        except:
            raise OSError("Cannot set priority, required modules not installed")

            
        pid = win32api.GetCurrentProcessId()
        handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, True, pid)
        
        if priority == "Low":
            win32process.SetPriorityClass(handle, win32process.BELOW_NORMAL_PRIORITY_CLASS)
        if priority == "Lowest":
            win32process.SetPriorityClass(handle, win32process.IDLE_NORMAL_PRIORITY_CLASS)
        elif priority == "Normal":
            win32process.SetPriorityClass(handle, win32process.NORMAL_PRIORITY_CLASS)
            
        return
        
    else:
        
        #linux mac
        import os
        try:
            import psutil
        except:
            raise OSError("Cannot set priority, psutil module not installed")

        this_process = psutil.Process(os.getpid())

        # Try here, because priority cannot be raised unless we are root.
        try:
            if priority == "Low":
                this_process.nice = 5     
            elif priority == "Lowest":
                this_process.nice = 19
            elif priority == "Normal":
                this_process.nice = 0
        except:
            sys.stderr.write("Cannot set priority; probably insufficient privilege")           
            
        if priority == "Lowest":
            this_process.set_ionice(psutil.IOPRIO_CLASS_IDLE)
        elif ("Normal", "Low" in priority):
            this_process.set_ionice(psutil.IOPRIO_CLASS_BE)

        return

def low():
    """ Process will execute with lower CPU priority """
    return _set_priority("Low")
def lowest():
    """ Process will only execute when system is idle """
    return _set_priority("Lowest")    
def normal():
    """ Process will try to reset to normal priority """
    return _set_priority("Normal")


