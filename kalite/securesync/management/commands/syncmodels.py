from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from securesync.api_client import SyncClient


class Command(BaseCommand):
    args = "<target server host (protocol://domain:port)>"
    help = "Synchronize the local SyncedModels with a remote server"

    def stdout_writeln(self, str):  self.stdout.write("%s\n"%str)
    def stderr_writeln(self, str):  self.stderr.write("%s\n"%str)
        
    def handle(self, *args, **options):

        self.stdout_writeln(("Checking purgatory for unsaved models")+"...")
        call_command("retrypurgatory")

        kwargs = {}
        if len(args) >= 1:
            kwargs["host"] = args[0]

        client = SyncClient(**kwargs)
        
        
        if client.test_connection() != "success":
            self.stderr_writeln(("KA Lite host is currently unreachable")+": %s" % client.url)
            return
        
        self.stdout_writeln(("Initiating SyncSession")+"...")
        result = client.start_session()
        if result != "success":
            self.stderr_writeln(("Unable to initiate session")+": %s" % result.content)
            return
                
        self.stdout_writeln(("Syncing models")+"...")
        
        while True:
            results = client.sync_models()
            
            # display counts for this block of models being transferred
            self.stdout_writeln("\t%s: %d (%d failed)" % (
                ("Uploaded"),
                results["upload_results"]["saved_model_count"],
                results["upload_results"]["unsaved_model_count"]))
            self.stdout_writeln("\t%s: %d (%d failed)" % (
                ("Downloaded"),
                results["download_results"]["saved_model_count"],
                results["download_results"]["unsaved_model_count"]))
            
            # count the number of successes and failures
            upload_results = results["upload_results"]
            download_results = results["download_results"]
            success_count = upload_results["saved_model_count"] + download_results["saved_model_count"]
            fail_count = upload_results["unsaved_model_count"] + download_results["unsaved_model_count"]
            
            # stop when nothing is being transferred anymore
            if success_count + fail_count == 0:
                break
        
        self.stdout_writeln("%s... (%s: %d, %s: %d)" % 
            (("Closing session"), ("Total uploaded"), client.session.models_uploaded, ("Total downloaded"), client.session.models_downloaded))

        self.stdout_writeln(("Checking purgatory once more, to try saving any unsaved models")+"...")
        call_command("retrypurgatory")
        
        client.close_session()
        