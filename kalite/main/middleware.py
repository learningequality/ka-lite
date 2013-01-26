from config.models import Settings

class GetNextParam:
	def process_request(self, request):
		next = request.GET.get("next", "")
		if next.startswith("/"):	
			request.next = next
		else:
			request.next = ""

# TODO(dylan): new class that handles finding and setting the language for the session
class SessionLanguage:
	def process_request(self, request):
		if "django_language" not in request.session:
			request.session["django_language"] = Settings.get("default_language")
	