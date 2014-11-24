import os

try:
    import local_settings
except ImportError:
    local_settings = object()


#######################
# Set module settings
#######################

# This must be a string type.
SETTINGS_KEY_EXAM_MODE = 'EXAM_MODE_ON'

STUDENT_TESTING_DATA_PATH = os.path.join(os.path.dirname(__file__), "data")
