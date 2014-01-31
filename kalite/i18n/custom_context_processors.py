from shared.i18n import lcode_to_ietf, get_language_name


def languages(request):
    if "default_language" not in request.session:
        return {}  # temporarily skipped middleware, but we'll get back here again.  Tricky Django...

    return {
        "default_language": lcode_to_ietf(request.session["default_language"]),
        "language_choices": request.session["language_choices"],
        "current_language": request.language,
        "current_language_native_name": get_language_name(request.language, native=True),
        "current_language_name": get_language_name(request.language),
    }
