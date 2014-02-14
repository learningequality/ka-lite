from annoying.functions import get_object_or_None

from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseServerError

from .devices.views import *
from securesync.models import SyncSession
from testing.asserts import distributed_server_only


@distributed_server_only
def crypto_login(request):
    """
    Remote admin endpoint, for login to a distributed server (given its IP address; see central/views.py:crypto_login)

    An admin login is negotiated using the nonce system inside SyncSession
    """
    if "client_nonce" in request.GET:
        client_nonce = request.GET["client_nonce"]
        try:
            session = SyncSession.objects.get(client_nonce=client_nonce)
        except SyncSession.DoesNotExist:
            return HttpResponseServerError("Session not found.")
        if session.server_device.is_trusted():
            user = get_object_or_None(User, username="centraladmin")
            if not user:
                user = User(username="centraladmin", is_superuser=True, is_staff=True, is_active=True)
                user.set_unusable_password()
                user.save()
            user.backend = "django.contrib.auth.backends.ModelBackend"
            auth_login(request, user)
        session.delete()
    return HttpResponseRedirect(reverse("homepage"))
