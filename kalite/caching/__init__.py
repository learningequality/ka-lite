"""
TODO: NOTHING SHOULD BE HERE! It's prohibiting the import of other caching.xxx
modules at load time because it has so many preconditions for loading.

For now, it means that caching.settings has been copied over to kalite.settings


Caching is a critical part of the KA Lite app, in order to speed up server response times.
However, if the server state changes, the cache may need to be invalidated.

This file exposes functions for clearing, or even pre-generating the cache.
It also implements listeners on some models to determine when the
cache needs to be invalidated.

For any app implementing cacheable data or writing to the web cache, the app should:
* Implement a CACHE_VARS variable, put cacheable variable values in there.  The values will be cleared,
    across all apps, by calling invalidate_inmemory_caches
* Call invalidate_web_cache (from fle_utils.internet.webcache)
"""
import os
import glob
import sys

from django.conf import settings; logging = settings.LOG
from django.core.urlresolvers import reverse
from django.test.client import Client

from fle_utils.internet.webcache import get_web_cache, has_cache_key, expire_page, caching_is_enabled, invalidate_web_cache
from kalite import i18n, topic_tools
from kalite.topic_tools.settings import DO_NOT_RELOAD_CONTENT_CACHE_AT_STARTUP, CHANNEL_DATA_PATH, CONTENT_CACHE_FILEPATH


def create_cache_entry(path=None, url_name=None, cache=None, force=False):
    """Create a cache entry"""

    assert (path or url_name) and not (path and url_name), "Must have path or url_name parameter, but not both"
    if not cache:
        cache = get_web_cache()

    if not path:
        path = reverse(url_name)
    if force and has_cache_key(path=path, cache=cache):
        expire_page(path=path)
        assert not has_cache_key(path=path, cache=cache)
    if not has_cache_key(path=path, cache=cache):
        Client().get(path)

    if not has_cache_key(path=path, cache=cache):
        logging.warn("Did not create cache entry for %s" % path)


def invalidate_inmemory_caches():
    """
    Any variables that are invalidated by things like content being added or deleted
    should be stored in the module's CACHE_VARS variable and registered here.

    This code clears all of those variables, so they are regenerated from scratch on
    the fly, using the new data.
    """
    # TODO: loop through all modules and see if a module variable exists, using getattr,
    #   rather than hard-coding.
    for module in (i18n, topic_tools):
        for cache_var in getattr(module, "CACHE_VARS", []):
            logging.debug("Emptying cache %s.%s" % (module.__name__, cache_var))
            setattr(module, cache_var, None)


def invalidate_all_caches():
    """
    Basic entry-point for clearing necessary caches.  Most functions can
    call in here.
    """
    invalidate_inmemory_caches()
    if DO_NOT_RELOAD_CONTENT_CACHE_AT_STARTUP:
        
        # The underlying assumption here is that if generating in memory caches is too onerous a task to conduct
        # at every system start up, then it is too onerous a task to conduct during server operation.
        # We defer the regeneration of these caches to next system startup, by deleting the existing disk based
        # copies of these caches.
        # This will prompt the caches to be recreated at next system start up, and the disk based copies to be rewritten.

        for filename in glob.glob(os.path.join(CHANNEL_DATA_PATH, "*.cache")) + [CONTENT_CACHE_FILEPATH]:
            os.remove(filename)
    elif sys.platform != 'darwin':
        # Macs have to run video download in a subprocess, and as this is only ever called during runtime from
        # video download or the videoscan subprocess, this never actually affects variables in the main KA Lite thread.
        initialize_content_caches(force=True)
    if caching_is_enabled():
        invalidate_web_cache()
    logging.debug("Great success emptying all caches.")

def initialize_content_caches(force=False):
    """
    Catch all function to regenerate any content caches in memory that need annotation
    with file availability
    """
    for lang in i18n.get_installed_language_packs(force=True).keys():
        logging.info("Preloading exercise data for language {lang}.".format(lang=lang))
        topic_tools.get_exercise_cache(force=force, language=lang)
        logging.info("Preloading content data for language {lang}.".format(lang=lang))
        topic_tools.get_content_cache(force=force, annotate=True, language=lang)
        logging.info("Preloading topic tree data for language {lang}.".format(lang=lang))
        topic_tools.get_topic_tree(force=force, annotate=True, language=lang)
