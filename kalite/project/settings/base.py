import warnings

# We do not care about the deprecation warning when this module has been
# imported because then people are probably doing things correctly

warnings.filterwarnings('ignore', message=r'kalite\.settings', append=True)

from kalite.settings import *  # @UnusedWildImport
