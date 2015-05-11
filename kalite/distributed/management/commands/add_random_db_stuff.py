"""
"""
import json
from django.core.management.base import BaseCommand, CommandError

from kalite.main.models import AssessmentBenchmarkModel

class Command(BaseCommand):
    def handle(self, *args, **options):
        for i in xrange(1,5000):
            a, found = AssessmentBenchmarkModel.objects.get_or_create(pk=i)
            if found:
                a.kind = "blah"
                a.item_data = json.dumps({"blah": "whatever"})
                a.author_names = str(["Michael Gallaspy"])
                a.sha = "yeahright"
                a.save()