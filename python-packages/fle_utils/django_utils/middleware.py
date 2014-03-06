"""
"""
from kalite.settings import LOG as logging


class GetNextParam:
    def process_request(self, request):
        next = request.GET.get("next", "")
        if next.startswith("/"):
            logging.debug("next='%s'" % next)
            request.next = next
        else:
            request.next = ""

