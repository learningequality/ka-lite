# Django serializers, for robustness when client/server/model versions are different
python-packages/django/core/serializers/base.py
    * django.core.serializers.base.py: added version_diff function, code to Serialize to skip serializing fields with a version greater than the client version
python-packages/django/core/serializers/python.py: added code to Deserialize to ignore errors in deserializing fields when the remote server has a newer version than the local server

python-packages/django/templates/base.py
    Purpose of the change: to enable "repeatblock",
    a template tag with the ability to repeat a block multiple times on a page.
    --- a/python-packages/django/template/base.py
    +++ b/python-packages/django/template/base.py
    @@ -230,11 +230,14 @@ class Parser(object):
             self.filters = {}
             for lib in builtins:
                 self.add_library(lib)
    +        self.root_nodelist = []

         def parse(self, parse_until=None):
             if parse_until is None:
                 parse_until = []
             nodelist = self.create_nodelist()
    +        #if self.root_nodelist is None:
    +        self.root_nodelist.append(nodelist)


python-packages/django/contrib/auth/forms.py: 139
    #Changed to modify username length from 30 to 75 (matching email addresses)
    +    username = forms.CharField(label=_("Username"), max_length=75) # tweaked for KA Lite (using email addr for username)

python-packages/django/contrib/auth/models.py: 232
    #Changed to modify username length from 30 to 75 (matching email addresses)
    +    username = models.CharField(_('username'), max_length=75, unique=True, # tweaked for KA Lite (use email for username)
    +        help_text=_('Required. 75 characters or fewer. Letters, numbers and '


python-packages/django/utils/cache.py:168
requires package additions:
import logging
from django.utils.translation import get_language_from_request
        # DJANGO_CHANGE(bcipolli)
        # The existing django logic here is completely different than the
        #   django translations pathway, which uses the more nuanced
        #   get_language_from_request.  For consistency and good interaction,
        #   cache should be using THAT.
        cache_key += '.%s' % get_language_from_request(request)


python-packages/django/utils/translation/trans_real.py:430
    # DJANGO_CHANGE(bcipolli):
    # run settings.LANGUAGE_CODE through same gauntlet as above
    # Otherwise, if we try to default to a sub-language (en-us), but only
    # the base language is installed (en), we'll get different behavior
    # based on client (some of which hit this fallback) IF the sub-language
    # is not installed.
    #
    # Since apps can't necessarily control that, we want the same fall-back
    # on LANGUAGE_CODE as for everything else.
    lang_code = settings.LANGUAGE_CODE

    if lang_code and lang_code not in supported:
        lang_code = lang_code.split('-')[0] # e.g. if fr-ca is not supported fallback to fr

    if lang_code and lang_code in supported and check_for_language(lang_code):
        return lang_code
    else:
        raise Exception("No language code could be determined; even fall-back on settings.LANGUAGE_CODE (%s) failed!" % settings.LANGUAGE_CODE)

diff --git a/python-packages/django/core/management/commands/test.py b/python-packages/django/core/management/commands/test.py
index 2b8e801..6349ed5 100644
--- a/python-packages/django/core/management/commands/test.py
+++ b/python-packages/django/core/management/commands/test.py
@@ -26,6 +26,14 @@ class Command(BaseCommand):
             help='Overrides the default address where the live server (used '
                  'with LiveServerTestCase) is expected to run from. The '
                  'default value is localhost:8081.'),
+        # DJANGO_CHANGE(aron):
+        # be able to support headless tests, which run PhantomJS
+        # instead of showing running a full-blown browser
+        make_option('--headless',
+                    action='store_true',
+                    default=False,
+                    dest='headless',
+                    help='Whether to run the browser tests in headless mode'),
     )
     help = ('Runs the test suite for the specified applications, or the '
             'entire site if no apps are specified.')
@@ -78,6 +86,15 @@ class Command(BaseCommand):
         from django.conf import settings
         from django.test.utils import get_runner

+        # DJANGO_CHANGE(aron):
+        # be able to support headless tests, which run PhantomJS
+        # instead of showing running a full-blown browser.
+        # Since there's no elegant way to pass options to testcases,
+        # we pass it through the settings module, with HEADLESS
+        # essentially acting as a global variable
+        if options.get('headless'):
+            settings.HEADLESS = True
+
         TestRunner = get_runner(settings, options.get('testrunner'))
         options['verbosity'] = int(options.get('verbosity'))

We extend clean_pyc so it will be automatically skipped when built by the build process
     def handle_noargs(self, **options):
+        from django.conf import settings
+        if settings.BUILT:
+            settings.LOG.info("Installation built by build process; skipping clean_pyc")
+            return
+
         project_root = options.get("path", None)
         if not project_root:
             project_root = get_project_root()
