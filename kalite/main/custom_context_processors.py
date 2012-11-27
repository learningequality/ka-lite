from django.conf import settings

def custom(request):
    return {
        "central_server_host": settings.CENTRAL_SERVER_HOST,
        "is_central": settings.CENTRAL_SERVER,
        "base_template": settings.CENTRAL_SERVER and "base_central.html" or "base_distributed.html",
    }
