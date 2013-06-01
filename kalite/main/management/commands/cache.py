import time
import logging
import sys

from django.core.management.base import BaseCommand, CommandError
from django.utils import translation

from kalite.main.models import VideoFile
from kalite.utils.videos import download_video, DownloadCancelled
from utils.jobs import force_job
from utils import caching
from kalite.main import topicdata
        

class Command(BaseCommand):
    help = "Manipulate the cache (create, show, clear)"
    
    def handle(self, *args, **options):
        cmd = sys.argv[2]
        if cmd in ["create", "recreate", "refresh"]:
            self.create_cache(force=(cmd in ["recreate", "refresh"]))
        elif cmd in ["show"]:
            self.show_cache()
        elif cmd in ["clear"]:
            self.clear_cache()
        else:
            raise NotImplementedError("Unknown option: %s" % cmd)
        
        
        

    def create_cache(self, force=False, path=None):
        """Go through each cacheable page, and either:
        (a) Cache each page that is not
        or
        (b) Kill and regenerate each page"""

        # Base case
        if path:
            if force:
                if caching.has_cache_key(path=path):
                    caching.expire_page(path=path)
                    print "[Redo] ",
                else:
                    print "[Miss] ",
                caching.create_cache(path=path)
                    
            else:
                if caching.has_cache_key(path=path):
                    print "[Hit!] ",
                else:
                    caching.create_cache(path=path)
                    print "[Miss] ",
                
            if caching.has_cache_key(path=path):
                print "\t%s" % path
            else: # should never get here!
                print "%s%s" % ("?"*10, path)
        
        # Recursive call
        else:

            print "Generating videos:"
            for v in topicdata.NODE_CACHE['Video'].values():
                self.create_cache(force=force, path=v['path'])
                 
            print "Generating exercises:"
            for e in topicdata.NODE_CACHE['Exercise'].values():
                self.create_cache(force=force, path=e['path'])

                
                
    def show_cache(self, path=None):
        """Go through each cacheable page, and show which are cached and which are NOT"""
        
        # Base case
        if path:
            if caching.has_cache_key(path=path):
                print "\t%s" % path
        
        else:
            print "Cached videos:"
            for v in topicdata.NODE_CACHE['Video'].values():
                self.show_cache(path=v['path'])
                
            print "Cached exercises:"
            for e in topicdata.NODE_CACHE['Exercise'].values():
                self.show_cache(path=e['path'])

       
                
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
            print "Clearing videos:"
            for v in topicdata.NODE_CACHE['Video'].values():
                self.clear_cache(path=v['path'])
                
            print "Clearing exercises:"
            for e in topicdata.NODE_CACHE['Exercise'].values():
                self.clear_cache(path=e['path'])
