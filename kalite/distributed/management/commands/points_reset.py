"""
"""
from django.core.management.base import BaseCommand, CommandError
from kalite.main.models import ExerciseLog, VideoLog, AttemptLog

class Command(BaseCommand):
    help = "Reset Points to zero for all the student accounts"

    def handle(self, *args, **options):
    	for entry in ExerciseLog.objects.all():
    		entry.points = 0
    		entry.save()
    	for entry in VideoLog.objects.all():
    		entry.points = 0
    		entry.save()
    	for entry in AttemptLog.objects.all():
    		entry.points = 0
    		entry.save()