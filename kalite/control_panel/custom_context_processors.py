from django.conf import settings
from config.models import Settings
from main.models import LanguagePack

def custom(request):
    return {
        "base_template": "central/base_central.html" if settings.CENTRAL_SERVER else "base_distributed.html",
        "is_central": settings.CENTRAL_SERVER,
    }

