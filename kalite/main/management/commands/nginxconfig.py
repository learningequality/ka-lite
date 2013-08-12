import os

from django.core.management.base import BaseCommand, CommandError
import settings

config_template = """

// In your local_settings.py file, set PRODUCTION_PORT = 7007
// Then, add the following to /etc/nginx/sites-enabled/kalite:

upstream kalite {
    server 127.0.0.1:7007;
}

proxy_cache_path  /var/cache/nginx levels=1:2 keys_zone=kalite:8m max_size=256m inactive=600m;
proxy_temp_path /var/cache/nginx/tmp;

server {

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

    location /favicon.ico {
        empty_gif;
    }

    location / {
        proxy_pass http://kalite;
        proxy_cache kalite;
    }

}


"""

class Command(BaseCommand):
    help = "Print recommended Nginx frontend proxy configuration file contents."

    def handle(self, *args, **options):
        self.stdout.write(config_template % {"root_path": os.path.realpath(settings.PROJECT_PATH + "/../")})
        
        
