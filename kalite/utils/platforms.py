"""
System = Windows, Linux, etc
Platform = WindowsXP-SP3, etc.

This file is for functions that take system- and platform-specific 
information, and try to make them accessible generically (at least for our purposes).
"""
import platform

def is_windows(system=None):
    system = system or platform.system()
    return system.lower() == "windows"


def is_osx(system=None):
    system = system or platform.system()
    return system.lower() == "darwin"


def system_script_extension(system=None):
    """
    The extension for the one script that could be considered "the os script" for the given system..
    """
    return ".bat" if is_windows(system) else ".sh"


def system_specific_scripts(system=None):
    """
    All scripting types for that platform, that wouldn't be recognized
    on ALL other platforms.
    """
    if is_windows(system):
        return [".bat", ".vbs"]
    elif is_osx(system):
        return [".command", ".sh"]
    else:
        return [".sh"]