import settings
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
        "restricted": settings.package_selected("UserRestricted")
    }


def languages(request):
    if "default_language" not in request.session:
        request.session["default_language"] = str(Settings.get("default_language") or "en")
    if "language_choices" not in request.session or request.is_admin:  # don't cache for admins
        request.session["language_choices"] = list(LanguagePack.objects.all())

    default_language = request.session["default_language"]
    return {
        "DEFAULT_LANGUAGE": default_language,
        "language_choices": request.session["language_choices"],
        "current_language": request.session.get("django_language", default_language),
    }

