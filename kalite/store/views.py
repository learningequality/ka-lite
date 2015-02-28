"""
"""
from annoying.decorators import render_to

from django.conf import settings; logging = settings.LOG

from kalite.shared.decorators.auth import require_login

@require_login
@render_to("store/store.html")
def store(request):
    return {}
