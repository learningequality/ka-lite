from django.conf import settings

def custom(request):
	return {
		'central_server_host': settings.CENTRAL_SERVER_HOST,
	}
