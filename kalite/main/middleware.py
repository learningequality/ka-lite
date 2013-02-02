from config.models import Settings
from django.contrib import messages
from django.http import HttpResponseRedirect

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
			request.session["django_language"] = Settings.get("default_language") or "en"
		if request.GET.get("set_language"):
			request.session["django_language"] = request.GET.get("set_language")
			return HttpResponseRedirect(request.path)
		if request.is_admin and request.GET.get("set_default_language"):
			Settings.set("default_language", request.GET.get("set_default_language"))
			return HttpResponseRedirect(request.path)