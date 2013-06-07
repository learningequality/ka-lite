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
from utils import caching

class Command(BaseCommand):
    
    def usage(self, argname):
        return """cache <command>
    View / manipulate the HTML cache. Pass one arg:
        
    create - generate any pages that haven't been cached already
    refresh - regenerate all pages
    show - show a list of urls that are currently in the cache
    clear - remove all items from the cache"""

    def command_error(self, msg):
        print "Error: %s" % msg
        exit(1)
        
    def handle(self, *args, **options):

        if not getattr(settings, "CACHES", None):
            self.command_error("caching is turned off (CACHES is None)")
        elif not getattr(settings, "CACHE_TIME", None):
            self.command_error(msg="caching is turned off (CACHE_TIME is zero or none)")
        
        
        cmd = sys.argv[2]
        if cmd in ["create", "recreate", "refresh"]:
            self.create_cache(force=(cmd in ["recreate", "refresh"]))
        elif cmd in ["show", "check"]:
            self.show_cache()
        elif cmd in ["clear", "delete"]:
            self.clear_cache()
        else:
            command_error("Unknown option: %s" % cmd)


    @decorator
    def for_all_nodes(f, **kwargs):
        import pdb; pdb.set_trace()     
        for type in ['Video', 'Exercise', 'Topic']:
            self.stdout.write("%ss:\n" % type)
            for n in topicdata.NODE_CACHE[type].values():
                f(path=n['path'])
                
    @for_all_nodes
    def create_cache(self, **kwargs):
        """Go through each cacheable page, and either:
        (a) Cache each page that is not
        or
        (b) Kill and regenerate each page"""

        # Base case
        if path:
            if force:
                if caching.has_cache_key(path=path):
                    caching.expire_page(path=path)
                    print "[Redo]\t%s" % path
                else:
                    print "[Miss]\t%s" % path
                caching.create_cache(path=path)
                    
            else:
                if not caching.has_cache_key(path=path):
                    caching.create_cache(path=path)
                    print "[Miss]\t%s" % path
                
            if not caching.has_cache_key(path=path):
                # should never get here!
                print "%s%s" % ("?"*10, path)
        
    @for_all_nodes(**kwargs) 
    def show_cache(self, **kwargs):
        """Go through each cacheable page, and show which are cached and which are NOT"""
        
        # Base case
        if path:
            if caching.has_cache_key(path=path):
                print "\t%s" % path

                
    def clear_cache(self, path=None):
        """Go through each cacheable page, and show which are cached and which are NOT"""
        
        # Base case
        if path:
            if caching.has_cache_key(path=path):
                print "\t%s" % path
                caching.expire_page(path=path)
            else:
                print "skipping %s" % path
        else:
            for type in ['Video', 'Exercise', 'Topic']:
                print "Clearing %ss:" % type
                for n in topicdata.NODE_CACHE[type].values():
                    self.clear_cache(path=n['path'])
                