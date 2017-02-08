"""
"""


class GetNextParam:
    def process_request(self, request):
        next = request.GET.get("next", "")
        request.next = (next.startswith("/") and next) or ""
