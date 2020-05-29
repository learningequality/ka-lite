from django.utils import six

if six.PY3:
    memoryview = memoryview
else:
    memoryview = buffer


# Disable all this stuff because we do not want unnecessary imports of system
# libraries that may break needlessly
# Ref: https://github.com/iiab/iiab/issues/1382
raise ImportError("Harmless: We do not support gis")