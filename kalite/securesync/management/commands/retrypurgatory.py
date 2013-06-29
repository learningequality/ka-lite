import json

from django.core.management.base import BaseCommand, CommandError

from securesync import model_sync
from securesync.models import ImportPurgatory


class Command(BaseCommand):
    help = "Retry importing the models that are floating in purgatory."

    def stdout_writeln(self, str):  self.stdout.write("%s\n"%str)
    def stderr_writeln(self, str):  self.stderr.write("%s\n"%str)
    
    def handle(self, *args, **options):
        
        purgatories = ImportPurgatory.objects.all()

        if not purgatories:
            self.stdout_writeln(("Purgatory is model-free! Congrats!"))
            return

        for purgatory in purgatories:

            self.stdout_writeln("%s (%d %s, %s #%d)..." %
                (("Attempting to save models"), 
                 purgatory.model_count, ("models"), 
                 ("attempt"), purgatory.retry_attempts))

            unsaved = model_sync.save_serialized_models(purgatory)["unsaved_model_count"]
            if not unsaved:
                self.stdout_writeln("\t%s :)"%(("All models were saved successfully!")))
            else:
                self.stderr_writeln("\t%d %s :(" % (unsaved,("models still did not save.  Check 'exceptions' field in 'input purgatory' for failure details.")))
