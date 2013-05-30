DEBUG=True
TEMPLATE_DEBUG=True

CENTRAL_SERVER_DOMAIN = "127.0.0.1:8001"
CENTRAL_SERVER_HOST   = "127.0.0.1:8001"
SECURESYNC_PROTOCOL   = "http"

"""
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'OPTIONS': {
            'read_default_file': PROJECT_PATH + "/database/my.cnf",
        },
    }
}
"""
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/var/tmp/django_cache',
        'TIMEOUT': 60,
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}
"""

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
        'TIMEOUT': 60,
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}
"""

