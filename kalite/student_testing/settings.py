import os

try:
    import local_settings
except ImportError:
    local_settings = object()


#######################
# Set module settings
#######################

STUDENT_TESTING_DATA_PATH = os.path.join(os.path.dirname(__file__), "data")
