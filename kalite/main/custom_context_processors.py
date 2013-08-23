from django.conf import settings
from config.models import Settings
from main.models import LanguagePack

def custom(request):
    return {
        "central_server_host": settings.CENTRAL_SERVER_HOST,
        "securesync_protocol": settings.SECURESYNC_PROTOCOL,
        "base_template": "base_distributed.html",
        "CONTENT_ROOT": settings.CONTENT_ROOT,
        "CONTENT_URL": settings.CONTENT_URL,
        "DATA_PATH": settings.DATA_PATH,
        "settings": settings,
        "is_central": False,
    }


def languages(request):
    default_language = Settings.get("default_language") or "en"
    return {
        "DEFAULT_LANGUAGE": default_language,
        "language_choices": LanguagePack.objects.all(),
        "current_language": request.session.get("django_language", default_language),
    }

