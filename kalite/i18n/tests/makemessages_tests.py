import os
import tempfile

from django.test import TestCase

from django.core.management import call_command


class MakemessagesTestCase(TestCase):
    """
    Quick and dirty tests to ensure that we have a functional CLI
    """
    
    def test_makemessages(self):
        """
        Run the `manage videoscan` command synchronously
        """
        cwd = os.getcwd()
        d = tempfile.mkdtemp()
        # Must contain a sub directory kalite/
        kalite_dir = os.path.join(d, "kalite")
        os.mkdir(kalite_dir)
        os.chdir(kalite_dir)
        os.mkdir(os.path.join(kalite_dir, "locale"))
        os.mkdir(os.path.join(kalite_dir, "templates"))
        f = open(os.path.join(kalite_dir, "templates", "test.html"), "w")
        f.write("""{% trans "Something for translation" %}""")
        f.close()
        try:
            call_command("makemessages", locale="en")
            f = open(os.path.join(kalite_dir, "locale", "en", "LC_MESSAGES", "django.po"), "r")
            self.assertIn("Something", f.read())
        finally:
            os.chdir(cwd)
