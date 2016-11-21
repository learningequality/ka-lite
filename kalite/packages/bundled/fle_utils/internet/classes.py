"""
For functions mucking with internet access
"""
import datetime
from django.db import models
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.utils import simplejson

class StatusException(Exception):
    """Class used for turning a HTTP response error into an exception"""
    def __init__(self, message, status_code):
        super(StatusException, self).__init__(message)
        self.args = (status_code,)
        self.status_code = status_code


class CsvResponse(HttpResponse):
    """Wrapper class for generating a HTTP response with CSV data"""
    def __init__(self, content, *args, **kwargs):
        assert isinstance(content, basestring)
        super(CsvResponse, self).__init__(content, content_type='text/csv', *args, **kwargs)


def _dthandler(obj):
    """Handler for object types that are not Json-serializable"""
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    elif hasattr(obj, "to_json"):
        return obj.to_json()
    else:
        return None


class JsonResponse(HttpResponse):
    """Wrapper class for generating a HTTP response with JSON data"""
    def __init__(self, content, *args, **kwargs):
        if isinstance(content, models.Model):
            # TODO(jamalex): write a wrapper for model_to_dict that filters out fields like sigs/counters/deletion
            content = model_to_dict(content)
        if not isinstance(content, basestring):
            content = simplejson.dumps(content, ensure_ascii=False, default=_dthandler)
        super(JsonResponse, self).__init__(content, content_type='application/json', *args, **kwargs)


class JsonResponseMessage(JsonResponse):
    def __init__(self, message, level="success", code=None, data={}, *args, **kwargs):

        # Set the content dictionary
        content = {level: unicode(message)}
        if code:
            data["code"] = code
        content.update(data)


        # Set status code.  TODO(bcipolli): this should always be 200, but
        #  so much script code counts on 500, hard to change
        if not "status" in kwargs:
            kwargs["status"] = 200 if level == "success" else 500

        super(JsonResponseMessage, self).__init__(content, *args, **kwargs)

class JsonResponseMessageSuccess(JsonResponseMessage):
    def __init__(self, *args, **kwargs):
        super(JsonResponseMessageSuccess, self).__init__(level="success", *args, **kwargs)

class JsonResponseMessageInfo(JsonResponseMessage):
    def __init__(self, *args, **kwargs):
        super(JsonResponseMessageInfo, self).__init__(level="info", *args, **kwargs)

class JsonResponseMessageError(JsonResponseMessage):
    def __init__(self, *args, **kwargs):
        super(JsonResponseMessageError, self).__init__(level="error", *args, **kwargs)

class JsonResponseMessageWarning(JsonResponseMessage):
    def __init__(self, *args, **kwargs):
        super(JsonResponseMessageWarning, self).__init__(level="warning", *args, **kwargs)

class JsonpResponse(HttpResponse):
    """Wrapper class for generating a HTTP response with JSONP data"""
    def __init__(self, content, callback, *args, **kwargs):
        if not isinstance(content, basestring):
            content = simplejson.dumps(content, ensure_ascii=False)
        # wrap the content in the callback function, to turn it into JSONP
        content = "%s(%s);" % (callback, content)
        super(JsonpResponse, self).__init__(content, content_type='application/javascript', *args, **kwargs)
