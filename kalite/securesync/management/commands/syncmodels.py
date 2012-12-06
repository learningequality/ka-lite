from django.core.management.base import BaseCommand, CommandError
from securesync.api_client import SyncClient

class Command(BaseCommand):
    args = "<target server host (protocol://domain:port)>"
    help = "Synchronize the local SyncedModels with a remote server"

    def handle(self, *args, **options):

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
        results = client.sync_models()
        while results["upload_results"]["saved_model_count"] + results["download_results"]["saved_model_count"] > 0:
            self.stdout.write("\tUploaded: %d (%d failed)\n" % (results["upload_results"]["saved_model_count"],
                                                    results["upload_results"]["unsaved_model_count"]))
            self.stdout.write("\tDownloaded: %d (%d failed)\n" % (results["download_results"]["saved_model_count"],
                                                    results["download_results"]["unsaved_model_count"]))
            results = client.sync_models()
        
        self.stdout.write("Closing session...\n(Uploaded: %d, Downloaded: %d)\n" % 
            (client.session.models_uploaded, client.session.models_downloaded))
        
        client.close_session()
        