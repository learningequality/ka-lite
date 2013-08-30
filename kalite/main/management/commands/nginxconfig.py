import os

from django.core.management.base import BaseCommand, CommandError
import settings

config_template = """

# In your local_settings.py file, set PRODUCTION_PORT = 7007
# Then, add the following to /etc/nginx/sites-enabled/kalite:

upstream kalite {
    server 127.0.0.1:7007;
}

server {

    # You may change the following port (8008) to something else,
    # if you want the website to be accessible at a different port:
    listen 8008;

    location /static {
        alias   %(root_path)s/kalite/static/;
    }

    location /media {
        alias   %(root_path)s/kalite/media/;
    }

    location /content {
        alias   %(root_path)s/content/;
    }

    location /api/v1 {
        types { }
        default_type "application/json";
        return 200 "{}";
    }

    location /favicon.ico {
        empty_gif;
    }

    location / {
        proxy_set_header Host $http_host;
        proxy_set_header X-Scheme $scheme;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_pass http://kalite;
    }

}

"""

class Command(BaseCommand):
    help = "Print recommended Nginx frontend proxy configuration file contents."

    def handle(self, *args, **options):
        self.stdout.write(config_template % {"root_path": os.path.realpath(settings.PROJECT_PATH + "/../")})
        
        
