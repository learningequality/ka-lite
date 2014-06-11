from . import lcode_to_ietf, get_language_name, get_installed_language_packs


def languages(request):
    if "default_language" not in request.session:
        return {}  # temporarily skipped middleware, but we'll get back here again.  Tricky Django...

    language_choices = get_installed_language_packs()

    return {
        "default_language": lcode_to_ietf(request.session["default_language"]),
        "language_choices": language_choices,
        "num_language_choices": len(language_choices),
        "current_language": request.language,
        "current_language_name": get_language_name(request.language),
    }
