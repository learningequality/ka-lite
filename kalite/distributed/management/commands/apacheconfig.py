"""
"""
import os

from django.conf import settings
from django.core.management.base import BaseCommand


config_template = """

Listen %(port)s

<VirtualHost *:%(port)s>

    Alias /static %(project_path)sstatic
    Alias /favicon.ico %(project_path)sstatic/images/favicon.ico

    <Directory %(project_path)s>
        Order deny,allow
        Allow from all
    </Directory>

    WSGIScriptAlias / %(project_path)ska-lite.wsgi

</VirtualHost>

"""

class Command(BaseCommand):
    help = "Print recommended Apache virtual host configuration file contents."

    def handle(self, *args, **options):
        self.stdout.write(config_template % {
            "project_path": settings.PROJECT_PATH,
            "port": settings.PRODUCTION_PORT,
        })

        # set the database permissions so that Apache will be able to access them
        database_file = settings.DATABASES["default"]["NAME"]
        if os.path.exists(database_file) and hasattr(os, "chmod"):
            database_dir = os.path.dirname(database_file)
            os.chmod(database_dir, 0777)
            os.chmod(database_file, 0766)
