"""
This is the command that does the actual syncing of models from distributed
servers to the central server, and back again.
"""
import time
from optparse import make_option

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from ...engine.api_client import SyncClient
from fle_utils import set_process_priority


class Command(BaseCommand):
    args = "<target server host (protocol://domain:port)> <num_retries>"
    help = "Synchronize the local SyncedModels with a remote server"

    option_list = BaseCommand.option_list + (
        make_option('-b', '--verbose',
            action='store_true',
            dest='verbose',
            default=False,
            help='Verbose display of syncing process.'),
    )

    def stdout_writeln(self, str):  self.stdout.write("%s\n"%str)
    def stderr_writeln(self, str):  self.stderr.write("%s\n"%str)

    def handle(self, *args, **options):
        if settings.CENTRAL_SERVER:
            raise CommandError("syncmodels cannot be run on the central server.")

        # Parse input parameters
        kwargs = {"host": args[0]} if len(args) >= 1 else {}
        max_retries = args[1] if len(args) >= 2 else 5

        set_process_priority.lowest(logging=settings.LOG)  # don't block users from web access due to syncing

        # Retry purgatory
        self.stdout_writeln(("Checking purgatory for unsaved models")+"...")
        call_command("retrypurgatory")

        client = SyncClient(verbose=options["verbose"], **kwargs)

        connection_status = client.test_connection()
        if connection_status != "success":
            self.stderr_writeln(("KA Lite host is currently unreachable") + " (%s): %s" % (connection_status, client.url))
            return

        self.stdout_writeln(("Initiating SyncSession")+"...")
        result = client.start_session()
        if result != "success":
            self.stderr_writeln(("Unable to initiate session")+": %s" % result.content)
            return

        self.stdout_writeln(("Syncing models")+"...")

        failure_tries = 0
        while True:
            results = client.sync_models()

            upload_results = results["upload_results"]
            download_results = results["download_results"]

            # display counts for this block of models being transferred
            self.stdout_writeln("\t%-15s: %d (%d failed, %d error(s))" % (
                ("Uploaded"),
                upload_results["saved_model_count"],
                upload_results["unsaved_model_count"],
                upload_results.has_key("error")))
            self.stdout_writeln("\t%-15s: %d (%d failed, %d error(s))" % (
                ("Downloaded"),
                download_results["saved_model_count"],
                download_results["unsaved_model_count"],
                download_results.has_key("error")))

            # count the number of successes and failures
            success_count = upload_results["saved_model_count"]   + download_results["saved_model_count"]
            fail_count    = upload_results["unsaved_model_count"] + download_results["unsaved_model_count"]
            error_count   = upload_results.has_key("error")       + download_results.has_key("error") + upload_results.has_key("exceptions")

            # Report any errors
            if error_count > 0:
                if upload_results.has_key("error"):
                    self.stderr_writeln("%s: %s" % (("Upload error"), upload_results["error"]))
                if download_results.has_key("error"):
                    self.stderr_writeln("%s: %s" % (("Download error"), download_results["error"]))
                if upload_results.has_key("exceptions"):
                    self.stderr_writeln("%s: %s" % (("Upload exceptions"), upload_results["exceptions"][:200]))

            # stop when nothing is being transferred anymore
            if success_count == 0 and (fail_count == 0 or failure_tries >= max_retries):
                break
            failure_tries += (fail_count > 0 and success_count == 0)

            # Allow the user to throttle the syncing by inserting a wait, so that users
            #   aren't overwhelmed by the computational need for signing during sync
            if settings.SYNCING_THROTTLE_WAIT_TIME is not None:
                time.sleep(settings.SYNCING_THROTTLE_WAIT_TIME)

        # Report summaries
        self.stdout_writeln("%s... (%s: %d, %s: %d, %s: %d)" %
            (("Closing session"), ("Total uploaded"), client.session.models_uploaded, ("Total downloaded"), client.session.models_downloaded, ("Total errors"), client.session.errors))

        # Report any exceptions
        if client.session.errors:
            self.stderr_writeln("Completed with %d errors." % client.session.errors)
        if failure_tries >= max_retries:
            self.stderr_writeln("%s (%d)." % ("Failed to upload all models (stopped after failed attempts)", failure_tries))

        self.stdout_writeln(("Checking purgatory once more, to try saving any unsaved models") + "...")
        call_command("retrypurgatory")

        client.close_session()

