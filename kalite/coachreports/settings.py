##############################
# Django settings
##############################

INSTALLED_APPS = (
    "django.contrib.auth",  # some views accessible to Django users
    "django.contrib.staticfiles",
    "fle_utils.django_utils",  # templatetags
    "kalite.facility",  # must come first, all other apps depend on this one.
    "kalite.main",  # *Log object queries
    "kalite.topic_tools",  # to organize by topic
    "kalite.testing",
)

MIDDLEWARE_CLASSES = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",  # used by distributed to authenticate admin (django) user
    "django.core.context_processors.request",  # expose request object within templates
)
