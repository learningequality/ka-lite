from django.core.management import call_command
from django.db import DatabaseError
from django.http import HttpResponse

from .models import Device
from fle_utils.config.models import Settings


class DBCheck:
    def process_request(self, request):
        if not request.session.get("install_validated"):
            try:
                count = Device.objects.count()
                request.session["install_validated"] = (count > 0)
            except DatabaseError:
                try:
                    call_command("migrate", merge=True)
                except DatabaseError:
                    return HttpResponse("Please run 'python manage.py syncdb' and create an administrator user, before running the server.")

class RegisteredCheck:
    def process_request(self, request):
        if not "registered" in request.session:
            request.session["registered"] = Device.get_own_device().is_registered()
