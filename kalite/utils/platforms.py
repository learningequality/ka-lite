import platform

def is_windows(system=None):
    if system is None:
        system = platform.system()
    return system.lower() == "windows"

def system_script_extension():
    return ".bat" if is_windows() else ".sh"

def system_specific_scripts(system=None):

    if is_windows(system):
        return [".bat", ".vbs"]
    else:
        return [".sh"]