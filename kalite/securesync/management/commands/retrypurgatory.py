from django.core.management.base import BaseCommand, CommandError
from securesync.models import ImportPurgatory, save_serialized_models

class Command(BaseCommand):
    help = "Retry importing the models that are floating in purgatory."

    def handle(self, *args, **options):
        
        purgatories = ImportPurgatory.objects.all()

        if not purgatories:
            self.stdout.write("Purgatory is model-free! Congrats!\n")
            return

        for purgatory in purgatories:
            self.stdout.write("Attempting to save %d models from %s (attempt #%d)...\n" %
                (purgatory.model_count, purgatory.timestamp, purgatory.retry_attempts))
            unsaved = save_serialized_models(purgatory)["unsaved_model_count"]
            if unsaved:
                self.stdout.write("\tThere were %d models that still did not save. :(\n")
            else:
                self.stdout.write("\tAll models were saved successfully! :)\n")
