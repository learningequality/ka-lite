try:
    import local_settings
except ImportError:
    local_settings = object()


#######################
# Set module settings
#######################

# Default facility name
INSTALL_FACILITY_NAME = getattr(local_settings, "INSTALL_FACILITY_NAME", None)  # default to None, so can be translated to latest language at runtime.

# None means, use full hashing locally--turn off the password cache
PASSWORD_ITERATIONS_TEACHER = getattr(local_settings, "PASSWORD_ITERATIONS_TEACHER", None)
PASSWORD_ITERATIONS_STUDENT = getattr(local_settings, "PASSWORD_ITERATIONS_STUDENT", None)
assert PASSWORD_ITERATIONS_TEACHER is None or PASSWORD_ITERATIONS_TEACHER >= 1, "If set, PASSWORD_ITERATIONS_TEACHER must be >= 1"
assert PASSWORD_ITERATIONS_STUDENT is None or PASSWORD_ITERATIONS_STUDENT >= 1, "If set, PASSWORD_ITERATIONS_STUDENT must be >= 1"

# This should not be set, except in cases where additional security is desired.
PASSWORD_ITERATIONS_TEACHER_SYNCED = getattr(local_settings, "PASSWORD_ITERATIONS_TEACHER_SYNCED", 5000)
PASSWORD_ITERATIONS_STUDENT_SYNCED = getattr(local_settings, "PASSWORD_ITERATIONS_STUDENT_SYNCED", 2500)
assert PASSWORD_ITERATIONS_TEACHER_SYNCED >= 5000, "PASSWORD_ITERATIONS_TEACHER_SYNCED must be >= 5000"
assert PASSWORD_ITERATIONS_STUDENT_SYNCED >= 2500, "PASSWORD_ITERATIONS_STUDENT_SYNCED must be >= 2500"

PASSWORD_CONSTRAINTS = getattr(local_settings, "PASSWORD_CONSTRAINTS", {
    'min_length': getattr(local_settings, 'PASSWORD_MIN_LENGTH', 6),
})


DISABLE_SELF_ADMIN = getattr(local_settings, "DISABLE_SELF_ADMIN", False)  #
