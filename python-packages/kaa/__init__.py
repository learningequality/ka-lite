# This is an auto-generated file.  Package maintainers: please ensure this
# file is packaged only with the kaa-base package if you are not packaging
# eggs.
try:
    try:
        __import__('pkg_resources').declare_namespace('kaa')
        __import__('pkg_resources').get_distribution('kaa-base').activate()
    except __import__('pkg_resources').DistributionNotFound:
        # kaa.base not yet installed
        pass
except ImportError:
    # setuptools not installed
    pass
from kaa.base import *
from kaa.base import __version__
