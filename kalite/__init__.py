# testing isn't always available; just ignore if not
try:
    import utils.testing.testrunner
except Exception as e:
    pass
try:
    import tests.loadtesting as loadtesting
except Exception as e:
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
