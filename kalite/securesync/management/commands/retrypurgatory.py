from django.core.management.base import BaseCommand, CommandError
from securesync.models import ImportPurgatory
from securesync import model_sync

class Command(BaseCommand):
    help = "Retry importing the models that are floating in purgatory."

    def handle(self, *args, **options):
        
        purgatories = ImportPurgatory.objects.all()

        if not purgatories:
            self.stdout.write("Purgatory is model-free! Congrats!\n")
            return

        for purgatory in purgatories:
            self.stdout.write("Attempting to save %d models (attempt #%d)...\n" %
                (purgatory.model_count, purgatory.retry_attempts))
            unsaved = model_sync.save_serialized_models(purgatory)["unsaved_model_count"]
            if unsaved:
                self.stdout.write("\t%d models still did not save. :(\n" % unsaved)
            else:
                self.stdout.write("\tAll models were saved successfully! :)\n")
