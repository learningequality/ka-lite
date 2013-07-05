import settings

def custom(request):
    return {
        "base_template": "central/base_central.html",
        "is_central": settings.CENTRAL_SERVER,
    }
