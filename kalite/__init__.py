from version import *

# testing isn't always available; just ignore if not
try:
    import testing.testrunner
except Exception as e:
    pass
try:
    import testing.loadtesting as loadtesting
except Exception as e:
    pass

try:
    import platform
    OS = ", ".join(platform.uname() + ("Python %s" % platform.python_version(),))
except:
    try:
        import sys
        OS = sys.platform
    except:
        OS = ""


