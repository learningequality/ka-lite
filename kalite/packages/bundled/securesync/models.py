# The sub-applications have a true django application layout
# but can never be used independently from their container model which is
# also an application of its own.
# This will cause possible overlapping table prefixing and potential hardships
# for the django load time model resolver.

from .devices.models import *
from .engine.models import *
