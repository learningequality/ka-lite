from shared.i18n import lcode_to_ietf


def languages(request):
    if "default_language" not in request.session:
        return {}  # temporarily skipped middleware, but we'll get back here again.  Tricky Django...

    return {
        "default_language": lcode_to_ietf(request.session["default_language"]),
        "language_choices": request.session["language_choices"],
        "current_language": lcode_to_ietf(request.session["django_language"]),
    }
