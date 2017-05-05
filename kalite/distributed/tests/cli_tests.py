import time


from django.test import TestCase
from thread import start_new_thread

from cherrypy import engine

from kalite import cli


class CLITestCase(TestCase):
    """
    Quick and dirty tests to ensure that we have a functional CLI
    """
    
    def test_manage(self):
        """
        Run the `manage videoscan` command synchronously
        """
        cli.manage("videoscan")

    def test_thread_manage(self):
        """
        Run the `manage help` command as thread
        """
        cli.manage("help", as_thread=True)

    def test_start(self):
        def cherry_py_stop_thread():
            time.sleep(15)
            engine.exit()

        # Because threads use the database with transactions, we can't run
        # the server in its own thread. Instead, we run `cli.start` from the
        # main thread and ask cherrypy to stop from a separate countdown
        # thread.
        start_new_thread(cherry_py_stop_thread, ())
        cli.start(
            debug=False,
            daemonize=False,
            args=[],
            skip_job_scheduler=True,
            port=8009,
        )
