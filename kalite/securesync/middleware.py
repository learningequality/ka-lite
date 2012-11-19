from django.core.management import call_command
from django.db import DatabaseError
from django.http import HttpResponse

from models import Device

class DBCheck:
    def process_request(self, request):
        try:
            count = Device.objects.count()
        except DatabaseError:
            try:
                call_command("migrate", merge=True)
            except DatabaseError:
                return HttpResponse("Please run 'python manage.py syncdb' to create an administrator user, before running the server.")

class AuthFlags:
    def process_request(self, request):
        request.is_admin = False
        request.is_teacher = False
        request.is_logged_in = False
        request.is_django_user = False

        if request.user.is_authenticated():
            request.is_logged_in = True
            request.is_django_user = True
            if request.user.is_superuser:
                request.is_admin = True
            if "facility_user" in request.session:
                del request.session["facility_user"]
        elif "facility_user" in request.session:
            if request.session["facility_user"].is_teacher:
                request.is_admin = True
                request.is_teacher = True
            request.is_logged_in = True

