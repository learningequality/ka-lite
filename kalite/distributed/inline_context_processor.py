"""
A context processor to enable or disable inline help. Adds context variable which enables/disables extra js assets.
"""

from kalite import settings

def inline(request):
    return {"inline_help": getattr(settings, "INLINE_HELP", False)}