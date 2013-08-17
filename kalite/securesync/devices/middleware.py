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
