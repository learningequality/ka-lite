########################
# Django dependencies
########################

INSTALLED_APPS = (
    "django.contrib.auth",  # some views only available to Django admins
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "fle_utils.django_utils",  # templatetags
    "kalite.facility",  # must come first, all other apps depend on this one.
    "kalite.coachreports",  # embedded into control_panel
    "kalite.topic_tools",  # for counting # of exercises
    "kalite.main",  # for summary stats on *Log
    "kalite.contentload",  # for students to download data from their personal control panel.
    "kalite.testing",
    "securesync",  # for querying objects
)

MIDDLEWARE_CLASSES = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",  # used by distributed to authenticate admin (django) user
    "django.core.context_processors.request",  # expose request object within templates
)
