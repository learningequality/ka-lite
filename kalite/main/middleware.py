class GetNextParam:
	def process_request(self, request):
		next = request.GET.get("next", "")
		if next.startswith("/"):	
			request.next = next
		else:
			request.next = ""

# TODO(dylan): new class that handles finding and setting the language for the session