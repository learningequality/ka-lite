import time
import logging
import sys
from decorator.decorator import decorator

from django.core.management.base import BaseCommand, CommandError
from django.utils import translation

import settings
from main import topicdata
from main.models import VideoFile
from utils.videos import download_video, DownloadCancelled
from utils.jobs import force_job
from utils import caching, topic_tools


class Command(BaseCommand):
    
    def usage(self, argname):
        return """cache <command>
    View / manipulate the HTML cache. Pass one arg:
        
    create - generate any pages that haven't been cached already
    refresh - regenerate all pages
    show - show a list of urls that are currently in the cache
    clear - remove all items from the cache"""


    def handle(self, *args, **options):

        if settings.CACHE_TIME == 0:
            raise CommandError("caching is turned off (CACHE_TIME is zero or none)")
        elif len(args)<1:
            raise CommandError("No command specified.")        
        cmd = args[0].lower()

        if cmd in ["create", "recreate", "refresh"]:
            self.create_cache(force=(cmd in ["recreate", "refresh"]))
        elif cmd in ["show", "check"]:
            self.show_cache()
        elif cmd in ["clear", "delete"]:
            self.clear_cache()
        else:
            raise CommandError("Unknown option: %s" % cmd)


    def create_cache(self, force=False):
        for node_type in ['Topic', 'Video', 'Exercise']:
            self.stdout.write("Caching %ss:\n" % node_type)
            for n in topicdata.NODE_CACHE[node_type].values():
                for path in n["paths"] if node_type in topic_tools.multipath_kinds else [n["path"]]:
                    self.create_page_cache(path=path, force=force)


    def create_page_cache(self, path, force=False):
        """Go through each cacheable page, and either:
        (a) Cache each page that is not
        or
        (b) Kill and regenerate each page"""

        if force:
            if caching.has_cache_key(path=path):
                caching.expire_page(path=path)
                self.stdout.write("[Redo]\t%s\n" % path)
            else:
                self.stdout.write("[Miss]\t%s\n" % path)
            caching.create_cache(path=path)
                
        else:
            if not caching.has_cache_key(path=path):
                caching.create_cache(path=path)
                self.stdout.write("[Miss]\t%s\n" % path)
            
        if not caching.has_cache_key(path=path):
            # should never get here!
            self.stdout.write("%s%s\n" % ("?"*10, path))

    def show_cache(self, force=False):
        """Go through each cacheable page, and show which are cached and which are NOT"""

        for node_type in ['Topic', 'Video', 'Exercise']:
            self.stdout.write("Cached %ss:\n" % node_type)
            for n in topicdata.NODE_CACHE[node_type].values():
                for path in n["paths"] if node_type in topic_tools.multipath_kinds else [n["path"]]:
                    if caching.has_cache_key(path=path):
                        self.stdout.write("\t%s\n" % path)
        
                
    def clear_cache(self):
        """Go through each cacheable page, and show which are cached and which are NOT"""

        for node_type in ['Topic', 'Video', 'Exercise']:
            self.stdout.write("Clearing %ss:\n" % node_type)
            for n in topicdata.NODE_CACHE[node_type].values():
                for path in n["paths"] if node_type in topic_tools.multipath_kinds else [n["path"]]:
                    if caching.has_cache_key(path=path):
                        self.stdout.write("\t%s\n" % path)
                        caching.expire_page(path=path)
