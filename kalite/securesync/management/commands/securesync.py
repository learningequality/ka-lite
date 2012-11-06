from django.core.management.base import BaseCommand, CommandError
from kalite.securesync.api_client import SyncClient

class Command(BaseCommand):
    args = "--host <target server host (protocol://domain:port)>"
    help = "Synchronize the local SyncedModels with a remote server"

    def handle(self, *args, **options):

        kwargs = {}

        if "host" in options:
            kwargs["host"] = options["host"]

        session = SyncClient(**kwargs)
        
        if session.test_connection() != "success":
            raise CommandError("Host is currently unreachable: %s" % session.url)
        
        self.stdout.write("Initiating SyncSession...\n")
        result = session.start_session()
        if result != "success":
            raise CommandError("Unable to initiate session: %s" % result.content)
        
        self.stdout.write("Syncing device records...\n")
        session.sync_device_records()
        
        self.stdout.write("Syncing models...\n")
        results = session.sync_models()
        self.stdout.write("\tUploaded: %d (%d failed)\n" % (results["upload_results"]["saved_model_count"],
                                                len(results["upload_results"]["unsaved_models"])))
        self.stdout.write("\tDownloaded: %d (%d failed)\n" % (results["download_results"]["saved_model_count"],
                                                len(results["download_results"]["unsaved_models"])))
        
        self.stdout.write("Closing session...\n")
        session.close_session()