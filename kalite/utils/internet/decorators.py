from django.core.exceptions import PermissionDenied

from .classes import CsvResponse, JsonResponse, JsonpResponse


def api_handle_error_with_json(handler):
    """
    All API requests should return JSON objects, even when unexpected errors occur.
    This decorator makes sure that all uncaught errors are not returned as HTML to the user, but instead JSON errors.
    """
    def wrapper_fn(*args, **kwargs):
        try:
            return handler(*args, **kwargs)
        except PermissionDenied as pe:
            raise pe  # handled upstream
        except Exception as e:
            return JsonResponse({"error": "Unexpected exception: %s" % e}, status=500)
    return wrapper_fn


def allow_jsonp(handler):
    """A general wrapper for API views that should be permitted to return JSONP.
    
    Note: do not use this on views that return sensitive user-specific data, as it
    could allow a 3rd-party attacker site to retrieve and store a user's information.

    Args:
        The api view, which must return a JsonResponse object, under normal circumstances.

    """
    def wrapper_fn(request, *args, **kwargs):
        
        response = handler(request, *args, **kwargs)
        
        # in case another type of response was returned for some reason, just pass it through
        if not isinstance(response, JsonResponse):
            return response

        if "callback" in request.REQUEST:
            
            if request.method == "GET":
                # wrap the JSON data as a JSONP response
                response = JsonpResponse(response.content, request.REQUEST["callback"])
            elif request.method == "OPTIONS":
                # return an empty body, for OPTIONS requests, with the headers defined below included
                response = HttpResponse("", content_type="text/plain")
            
            # add CORS-related headers, if the Origin header was included in the request
            if request.method in ["OPTIONS", "GET"] and "HTTP_ORIGIN" in request.META:
                response["Access-Control-Allow-Origin"] = request.META["HTTP_ORIGIN"]
                response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
                response["Access-Control-Max-Age"] = "1000"
                response["Access-Control-Allow-Headers"] = "Authorization,Content-Type,Accept,Origin,User-Agent,DNT,Cache-Control,X-Mx-ReqToken,Keep-Alive,X-Requested-With,If-Modified-Since"
        
        return response
        
    return wrapper_fn