Caching is a way for the web server to be more efficient in its responses, by serving stored results computed while serving a previous request, rather than recomputing it.  The major challenge with caching is: when do you invalidate your cache items (and force the server to recompute the result)?

## Overview

KA Lite caches in two different ways:
* per thread: For each server thread, listening for HTTP requests, keep some data in memory.
* global: Store server responses and data to disk, or to the database.

For each, we cache different information:
* per thread: [[the topic tree]]
* global: content pages (e.g. Homepage, topic pages, video pages, exercise pages) and search resources (`flat_topic_tree`)

Because per-thread caching is covered in [[the topic tree]], the focus here is on global caching.

## Code

In Django, requested urls are forwarded to views, which generate some context, hand it off to a template, and return a HttpResponse that contains output HTML.  

[Django caching](https://docs.djangoproject.com/en/dev/topics/cache/) caches both the headers and response body of that HttpResponse

### Cache back-end

Items that are stored in the cache are put into specific back-ends.  We use a file-based back-end by default.

### Cache key

In order to look up an item in the cache, a cache key is computed.  We use Django's default key function.

Cache entries include the following in their cache key:
* Request language
* Other things I'm unaware of


### Adding cache items

Our caching code resides `shared/caching.py`, and is used in multiple locations.  Below we define each function in `shared/caching.py` by the functional use of the cache.

`main/views.py` - uses functions for caching content pages

`backend_cache_page` is decorator applied to each cachable view. It uses Django's cache framework to detect cache cache hits and set appropriate headers in the response object.

In our code, we use the Django caching framework.

### Detecting changes

`backend_cache_page` only adds cache entries; however, when new resources are added, we need to clear the cache.

Unfortunately, while we have central functions that clear items from the cache, we don't have a centralized place for checking if an item has been invalidated.  Instead, much of the code requires the coder to remember to explicitly check whether an action would lead to a resource change that requires any cache items to be invalidated.

There are a number of items that invalidate pages:

* videos - videos can change on disk, or video metadata can change in the database.  Each case is handled differently.

* new subtitles - Subtitles are displayed on the topic page that contains videos or exercises.  

* translated exercises - NYI

### Viewing cache items

### Clearing cache items

