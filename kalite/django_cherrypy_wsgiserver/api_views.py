import os

from django.http import HttpResponse


def getpid(request):
    """
    who am I?  return the PID; used to kill the webserver process if the PID file is missing.
    """
    try:
        return HttpResponse(os.getpid())
    except:
        return HttpResponse("")
