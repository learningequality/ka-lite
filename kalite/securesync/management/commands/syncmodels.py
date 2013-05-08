from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from securesync.api_client import SyncClient

from django.utils.translation import ugettext as _

class Command(BaseCommand):
    args = "<target server host (protocol://domain:port)> <num_retries>"
    help = "Synchronize the local SyncedModels with a remote server"

    def stdout_writeln(self, str):  self.stdout.write("%s\n"%str)
    def stderr_writeln(self, str):  self.stderr.write("%s\n"%str)
        
    def handle(self, *args, **options):

        self.stdout_writeln(_("Checking purgatory for unsaved models")+"...")
        call_command("retrypurgatory")

        kwargs = {}
        if len(args) >= 1:
            kwargs["host"] = args[0]
        if len(args) >= 2:
            max_retries = args[1]
        else:
            max_retries = 5
            
        client = SyncClient(**kwargs)
        
        
        if client.test_connection() != "success":
            self.stderr_writeln(_("KA Lite host is currently unreachable")+": %s" % client.url)
            return
        
        self.stdout_writeln(_("Initiating SyncSession")+"...")
        result = client.start_session()
        if result != "success":
            self.stderr_writeln(_("Unable to initiate session")+": %s" % result.content)
            return
                
        self.stdout_writeln(_("Syncing models")+"...")
        
        failure_tries = 0
        while True:
            results = client.sync_models()
            upload_results = results["upload_results"]
            download_results = results["download_results"]

            #import pdb;pdb.set_trace()
            # display counts for this block of models being transferred
            self.stdout_writeln("\t%-15s: %d (%d failed, %d error(s))" % (
                _("Uploaded"),
                upload_results["saved_model_count"],
                upload_results["unsaved_model_count"],
                upload_results.has_key("error")))
            self.stdout_writeln("\t%-15s: %d (%d failed, %d error(s))" % (
                _("Downloaded"),
                download_results["saved_model_count"],
                download_results["unsaved_model_count"],
                download_results.has_key("error")))
            
            # count the number of successes and failures
            success_count = upload_results["saved_model_count"]  + download_results["saved_model_count"]
            fail_count    = upload_results["unsaved_model_count"] + download_results["unsaved_model_count"]
            error_count   = upload_results.has_key("error")       + download_results.has_key("error") + upload_results.has_key("exceptions")
            
            # Report any errors
            if error_count > 0:
                if upload_results.has_key("error"):
                    self.stderr_writeln("%s: %s"%(_("Upload error"),upload_results["error"]))
                if download_results.has_key("error"):
                    self.stderr_writeln("%s: %s"%(_("Download error"),download_results["error"]))
                if upload_results.has_key("exceptions"):
                    self.stderr_writeln("%s: %s"%(_("Upload exceptions"),upload_results["exceptions"][:100]))

            # stop when nothing is being transferred anymore
            if success_count == 0 and (fail_count == 0 or failure_tries >= max_retries):
                break
            failure_tries += (fail_count > 0 and success_count == 0)
            
        # Report summaries
        self.stdout_writeln("%s... (%s: %d, %s: %d, %s: %d)" % 
            (_("Closing session"), _("Total uploaded"), client.session.models_uploaded, _("Total downloaded"), client.session.models_downloaded, _("Total errors"), client.session.errors))

        # Report any exceptions
        if client.session.errors:
            self.stderr_writeln("Completed with %d errors."%client.session.errors)
        if failure_tries >= max_retries:
            self.stderr_writeln("%s (%d)."%("Failed to upload all models (stopped after failed attempts)",failure_tries))
            if upload_results.has_key("exceptions"):
                self.stderr_writeln("Upload exceptions: %s"%upload_results["exceptions"])
            
        self.stdout_writeln(_("Checking purgatory once more, to try saving any unsaved models")+"...")
        call_command("retrypurgatory")
        
        client.close_session()
        