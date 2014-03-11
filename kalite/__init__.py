# suppress warnings here.
try:
    import warnings
    warnings.simplefilter("ignore") # any other filter was ineffecual or threw an error
except:
    pass

from version import *
