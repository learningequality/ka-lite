from django.core.management.base import BaseCommand, CommandError
import settings

config_template = """

Listen 8002

<VirtualHost *:8002>
    
    Alias /static %(project_path)s/static
    Alias /favicon.ico %(project_path)s/static/images/favicon.ico
    
    <Directory %(project_path)s>
        Order deny,allow
        Allow from all
    </Directory>

    WSGIScriptAlias / %(project_path)s/ka-lite.wsgi

</VirtualHost>

"""

class Command(BaseCommand):
    help = "Print recommended Apache virtual host configuration file contents."

    def handle(self, *args, **options):
        self.stdout.write(config_template % {"project_path": settings.PROJECT_PATH})
