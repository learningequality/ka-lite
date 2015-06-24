"""
This is the future main module for kalite settings, where all fundamental and
common django setttings should go.

However, since we are still supporting an old location of settings, we have not
put anything here.


...yet
"""
import warnings

# We do not care about the deprecation warning when this module has been
# imported because then people are probably doing things correctly

warnings.filterwarnings('ignore', message=r'.*Wrong settings module imported.*', append=True)

from kalite.settings import *  # @UnusedWildImport
