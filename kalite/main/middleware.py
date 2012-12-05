class GetNextParam:
	def process_request(self, request):
		next = request.GET.get("next", "")
		if next.startswith("/"):	
			request.next = next
		else:
			request.next = ""