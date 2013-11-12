def languages(request):
    if not "default_language" in request.session:  # Crazy Django sometimes calls this before the middleware, then will call this AGAIN afterwards
        return {}
    return {
        "DEFAULT_LANGUAGE": request.session["default_language"],
        "language_choices": request.session["language_choices"],
        "current_language": request.session["django_language"],
    }

