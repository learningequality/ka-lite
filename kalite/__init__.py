# testing isn't always available; just ignore if not
try:
    import tests.testrunner
    import tests.loadtesting
except:
    pass
    
import version
VERSION = version.VERSION

try:
    import platform
    OS = ", ".join(platform.uname() + ("Python %s" % platform.python_version(),))
except:
    try:
        import sys
        OS = sys.platform
    except:
        OS = ""
