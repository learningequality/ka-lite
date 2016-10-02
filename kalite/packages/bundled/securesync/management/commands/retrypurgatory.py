from django.core.management.base import BaseCommand

from ...engine.utils import save_serialized_models
from ...models import ImportPurgatory


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

            # Serialized version is ourselves (or an earlier version of ourselves),
            #   so say so explicitly to make sure errors get bubbled up to us properly.
            try:
                unsaved = save_serialized_models(data=purgatory)["unsaved_model_count"]
                if not unsaved:
                    self.stdout_writeln("\t%s :)" % (("All models were saved successfully!")))
                else:
                    self.stderr_writeln("\t%d %s" % (unsaved,("models still did not save.  Check 'exceptions' field in 'input purgatory' for failure details.")))
            except Exception as e:
                self.stderr_writeln("\t%s %s" % (("Unexpected error saving models: "), e))
