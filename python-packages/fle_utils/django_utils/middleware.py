"""
"""
from django.conf import settings


class GetNextParam:
    def process_request(self, request):
        next = request.GET.get("next", "")
        request.next = (next.startswith("/") and next) or ""


class JsonAsHTML(object):
    '''
    View a JSON response in your browser as HTML
    Useful for viewing stats using Django Debug Toolbar

    This middleware should be place AFTER Django Debug Toolbar middleware
    '''

    def process_response(self, request, response):

        #not for production or production like environment
        if not settings.DEBUG:
            return response

        #do nothing for actual ajax requests
        if request.is_ajax():
            return response

        #only do something if this is a json response
        if "application/json" in response['Content-Type'].lower():
            title = "JSON as HTML Middleware for: %s" % request.get_full_path()
            response.content = "<html><head><title>%s</title></head><body>%s</body></html>" % (title, response.content)
            response['Content-Type'] = 'text/html'
        return response