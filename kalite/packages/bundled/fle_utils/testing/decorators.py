from django.conf import settings


def allow_api_profiling(handler):
    """
    For API requests decorated with this decorator,
    if 'debug' is passed in with DEBUG=True,
    it will add a BODY tag to the json response--allowing
    the debug_toolbar to be used.
    """
    if not settings.DEBUG:
        # for efficiency reasons, just return the API function when not in DEBUG mode.
        return handler
    else:
        def aap_wrapper_fn(request, *args, **kwargs):
            response = handler(request, *args, **kwargs)
            if not request.is_ajax() and response["Content-Type"] == "application/json":
                # Add the "body" tag, which allows the debug_toolbar to attach
                response.content = "<body>%s</body>" % response.content
                response["Content-Type"] = "text/html"
            return response
        return aap_wrapper_fn

