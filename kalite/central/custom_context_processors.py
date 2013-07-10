import settings

def custom(request):
    return {
        "base_template": "central/base.html",
        "is_central": True,
    }
