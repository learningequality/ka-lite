#from django.conf import settings
from config.models import Settings
from main.models import LanguagePack

def custom(request):
    return {
        "central_server_host": Settings.get("CENTRAL_SERVER_HOST"),
        "is_central": Settings.get("CENTRAL_SERVER"),
        "base_template": Settings.get("CENTRAL_SERVER") and "base_central.html" or "base_distributed.html",
        "CONTENT_ROOT": Settings.get("CONTENT_ROOT"),
        "CONTENT_URL": Settings.get("CONTENT_URL"),
        "DATA_PATH": Settings.get("DATA_PATH"),
    }


def languages(request):
	return {
		"DEFAULT_LANGUAGE": Settings.get("default_language") or "en",
        "language_choices": LanguagePack.objects.all(),
        "current_language": request.session.get("django_language"),
	}
