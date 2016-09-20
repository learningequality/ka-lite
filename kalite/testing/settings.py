import os

try:
    from kalite import local_settings
except ImportError:
    local_settings = object()


#######################
# Set module settings
#######################


KALITE_TEST_RUNNER = __package__ + ".testrunner.KALiteTestRunner"

RUNNING_IN_TRAVIS = bool(os.environ.get("TRAVIS"))

TESTS_TO_SKIP = getattr(local_settings, "TESTS_TO_SKIP", ["medium", "long"])  # can be
assert not (set(TESTS_TO_SKIP) - set(["short", "medium", "long"])), "TESTS_TO_SKIP must contain only 'short', 'medium', and 'long'"

AUTO_LOAD_TEST = getattr(local_settings, "AUTO_LOAD_TEST", False)
