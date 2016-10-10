# THIS IS USED BY settings.py.  NEVER import settings.py here; hard-codes only!
# Must be PEP 440 compliant: https://www.python.org/dev/peps/pep-0440/
# Must also be of the form N.N.N for internal use, where N is a non-negative integer
MAJOR_VERSION = "0"
MINOR_VERSION = "17"
PATCH_VERSION = "0b2"
VERSION = "%s.%s.%s" % (MAJOR_VERSION, MINOR_VERSION, PATCH_VERSION)
SHORTVERSION = "%s.%s" % (MAJOR_VERSION, MINOR_VERSION)


def user_agent():
    """
    HTTP User-Agent header string derived from version, used by various HTTP
    requests sent to learningequality.org for stats
    """
    from requests.utils import default_user_agent
    return "ka-lite/%s " % VERSION + default_user_agent()
