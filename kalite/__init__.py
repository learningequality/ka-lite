# suppress warnings here.
try:
    import warnings
    warnings.simplefilter("ignore") # any other filter was ineffecual or threw an error
except:
    pass

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
