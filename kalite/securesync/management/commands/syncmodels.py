from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from securesync.api_client import SyncClient

class Command(BaseCommand):
    args = "<target server host (protocol://domain:port)>"
    help = "Synchronize the local SyncedModels with a remote server"

    def handle(self, *args, **options):

        self.stdout.write("Checking purgatory for unsaved models...\n")
        call_command("retrypurgatory")

        kwargs = {}

        if len(args) >= 1:
            kwargs["host"] = args[0]

        client = SyncClient(**kwargs)
        
        if client.test_connection() != "success":
            self.stderr.write("KA Lite host is currently unreachable: %s\n" % client.url)
            return
        
        self.stdout.write("Initiating SyncSession...\n")
        result = client.start_session()
        if result != "success":
            self.stderr.write("Unable to initiate session: %s\n" % result.content)
            return
                
        self.stdout.write("Syncing models...\n")
        
        while True:
            results = client.sync_models()
            
            # display counts for this block of models being transferred
            self.stdout.write("\tUploaded: %d (%d failed)\n" % (
                results["upload_results"]["saved_model_count"],
                results["upload_results"]["unsaved_model_count"]))
            self.stdout.write("\tDownloaded: %d (%d failed)\n" % (
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
        
        self.stdout.write("Closing session... (Total uploaded: %d, Total downloaded: %d)\n" % 
            (client.session.models_uploaded, client.session.models_downloaded))

        self.stdout.write("Checking purgatory once more, to try saving any unsaved models...\n")
        call_command("retrypurgatory")
        
        client.close_session()
        