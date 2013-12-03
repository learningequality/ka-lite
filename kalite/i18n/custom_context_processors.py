def languages(request):
    if "default_language" not in request.session:
        return {}  # temporarily skipped middleware, but we'll get back here again.  Tricky Django...

    return {
        "default_language": request.session["default_language"],
        "language_choices": request.session["language_choices"],
        "current_language": request.session["django_language"],
    }

