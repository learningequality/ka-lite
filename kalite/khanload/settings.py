########################
# Django dependencies
########################

INSTALLED_APPS = (
    "kalite.facility",  # for authentication and data saving
    "kalite.main", # topic_tools
)

MIDDLEWARE_CLASSES = (
    "django.middleware.csrf.CsrfViewMiddleware",  # views expect csrf token
)