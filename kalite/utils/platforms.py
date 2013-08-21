import platform

def is_windows(platform=None):
    if platform is None:
        platform.system()
    return platform.system() == "windows"

def platform_script_extension():
    return ".bat" if is_windows() else ".sh"

def platform_specific_scripts(platform=None):

    if is_windows(platform):
        return [".bat", ".vbs"]
    else:
        return [".sh"]