from config.models import Settings
from shared.i18n import lcode_to_ietf, get_language_name, get_installed_language_packs

def languages(request):
    return {
        "default_language": lcode_to_ietf(request.session.get("default_language") or Settings.get("default_language") or "en"),
        "language_choices": request.session.get('language_choices') or get_installed_language_packs(),
        "current_language": request.language,
        "current_language_native_name": get_language_name(request.language, native=True),
        "current_language_name": get_language_name(request.language),
    }
