########################
# Django dependencies
########################

INSTALLED_APPS = (
    "kalite.facility",  # for authentication and data saving
    "kalite.main", # creating and saving data objects from Khan Academy data
    "kalite.topic_tools", # topic_tools
)

MIDDLEWARE_CLASSES = (
    "django.middleware.csrf.CsrfViewMiddleware",  # views expect csrf token
)