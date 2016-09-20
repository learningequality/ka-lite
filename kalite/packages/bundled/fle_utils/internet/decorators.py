import csv
import json
import traceback
from cStringIO import StringIO

from annoying.decorators import wraps

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, Http404
from django.utils.translation import ugettext as _
from .classes import CsvResponse, JsonResponse, JsonResponseMessageError, JsonpResponse

logger = settings.LOG


def api_handle_error_with_json(handler):
    """
    All API requests should return JSON objects, even when unexpected errors occur.
    This decorator makes sure that all uncaught errors are not returned as HTML to the user, but instead JSON errors.
    """
    def api_handle_error_with_json_wrapper_fn(request, *args, **kwargs):
        try:
            return handler(request, *args, **kwargs)
        except PermissionDenied:
            raise  # handled upstream
        except Http404:
            raise
        except Exception as e:
            logger.error("Error in JSON view: {}".format(request.path))
            traceback.print_exc()
            return JsonResponseMessageError(_("Unexpected error: %(err)s") % {"err": e}, status=500)
    return api_handle_error_with_json_wrapper_fn


def allow_jsonp(handler):
    """A general wrapper for API views that should be permitted to return JSONP.

    Note: do not use this on views that return sensitive user-specific data, as it
    could allow a 3rd-party attacker site to retrieve and store a user's information.

    Args:
        The api view, which must return a JsonResponse object, under normal circumstances.

    """
    def allow_jsonp_wrapper_fn(request, *args, **kwargs):
        if "callback" in request.REQUEST and request.method == "OPTIONS":
            # return an empty body, for OPTIONS requests, with the headers defined below included
            response = HttpResponse("", content_type="text/plain")

        else:
            response = handler(request, *args, **kwargs)

            if not isinstance(response, JsonResponse):
                # in case another type of response was returned for some reason, just pass it through
                return response
            elif "callback" in request.REQUEST:
                # wrap the JSON data as a JSONP response
                response = JsonpResponse(response.content, request.REQUEST["callback"])

        # add CORS-related headers, if the Origin header was included in the request
        if "callback" in request.REQUEST and request.method in ["OPTIONS", "GET"] and "HTTP_ORIGIN" in request.META:
            response["Access-Control-Allow-Origin"] = request.META["HTTP_ORIGIN"]
            response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            response["Access-Control-Max-Age"] = "1000"
            response["Access-Control-Allow-Headers"] = "Authorization,Content-Type,Accept,Origin,User-Agent,DNT,Cache-Control,X-Mx-ReqToken,Keep-Alive,X-Requested-With,If-Modified-Since"

        return response

    return allow_jsonp_wrapper_fn


def render_to_csv(context_keys, delimiter=",", key_label="key", order="stacked"):
    """
    "context_keys" are dictionary keys into the context object.
    We can have multiple keys, assuming that:
    * Each key returns a dict
    * Each dict has exactly the same keys (order doesn't matter)

    TODO(bcipolli): This won't work properly for unicode names.
    """
    def render_to_csv_renderer(function):
        @wraps(function)
        def render_to_csv_renderer_wrapper(request, *args, **kwargs):
            """
            The header row are all the keys from all the context_key dicts.
            The rows are accumulations of data across all the context_key dicts,
               one row per entry in the dict.
            """
            output = function(request, *args, **kwargs)
            if not isinstance(output, dict) or request.GET.get("format") != "csv":
                return output

            output_string = StringIO()
            writer = csv.writer(output_string, delimiter=delimiter, quoting=csv.QUOTE_MINIMAL)

            if order == "stacked":
                # Stack vertically
                ri = 0
                for context_key in context_keys:
                    for row_label, row_data in output[context_key].iteritems():
                        if ri == 0:
                            col_labels = [key_label] + row_data.keys()
                            writer.writerow(col_labels)
                        writer.writerow([row_label] + row_data.values())
                        ri += 1
                    # add blank line between types
                    writer.writerow([])

            elif order == "neighbors":
                # Stack horizontally
                row_labels = output[context_keys[0]].keys()
                col_labels = [key_label] + [kk for k in context_keys for kk in output[k][row_labels[0]].keys()]
                writer.writerow(col_labels)

                for ri, row_label in enumerate(row_labels):
                    row_data = [row_label]
                    for k in context_keys:
                        row_data += output[k][row_label].values()
                    writer.writerow(row_data)

            return CsvResponse(output_string.getvalue())
        return render_to_csv_renderer_wrapper
    return render_to_csv_renderer


def api_response_causes_reload(api_request_handler):
    @api_handle_error_with_json
    def api_response_causes_reload_wrapper_fn(request, *args, **kwargs):
        """If it's a non-error message, the page will reload, so add to messages instead of an AJAX response"""
        response = api_request_handler(request, *args, **kwargs)
        for msg_type, msg_text in json.loads(response.content).iteritems():
            if msg_type not in ["error"]:  # Only error should prevent the page from reloading
                fn = getattr(messages, msg_type)
                fn(request, msg_text)
        return response
    return api_response_causes_reload_wrapper_fn
