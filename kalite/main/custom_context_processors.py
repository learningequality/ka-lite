from django.conf import settings
from config.models import Settings
from main.models import LanguagePack

def custom(request):
    return {
        "central_server_host": settings.CENTRAL_SERVER_HOST,
        "base_template": "base_distributed.html",
        "CONTENT_ROOT": settings.CONTENT_ROOT,
        "CONTENT_URL": settings.CONTENT_URL,
        "DATA_PATH": settings.DATA_PATH,
        "settings": settings,
    }


def languages(request):
	return {
		"DEFAULT_LANGUAGE": Settings.get("default_language") or "en",
        "language_choices": LanguagePack.objects.all(),
        "current_language": request.session.get("django_language"),
	}
