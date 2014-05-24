import os

try:
    import local_settings
except ImportError:
    local_settings = object()


#######################
# Set module settings
#######################

STUDENT_TESTING_DATA_PATH = os.path.join(os.path.dirname(__file__), "data")

MIDDLEWARE_CLASSES = getattr(local_settings, 'MIDDLEWARE_CLASSES', tuple())
MIDDLEWARE_CLASSES = (
    "kalite.student_testing.middleware.ExamModeCheck",
) + MIDDLEWARE_CLASSES