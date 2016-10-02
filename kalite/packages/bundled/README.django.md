## BEGIN(djallado): Changes in makemessages.py and trans_real.py to generate handlebars templates in djangojs.pot file.
diff --git a/python-packages/django/core/management/commands/makemessages.py b/python-packages/django/core/management/commands/makemessages.py
index 2fd5bda..526026b 100644
--- a/python-packages/django/core/management/commands/makemessages.py
+++ b/python-packages/django/core/management/commands/makemessages.py
@@ -137,23 +137,7 @@ def process_file(file, dirpath, potfile, domain, verbosity,
     from django.utils.translation import templatize

     _, file_ext = os.path.splitext(file)
-
-    # DJANGO_CHANGE(cpauya):
-    # Handlebars templates must be processed like a Django template but
-    # must be saved into `djangojs.po` so we refactor the if conditions below.
-
-    is_file_ext_in_extensions = file_ext in extensions
-
-    is_handlebars = False
-    if is_file_ext_in_extensions and 'handlebars' in file_ext:
-        is_handlebars = True
-
-    if is_handlebars and domain != 'djangojs':
-        stdout.write('You must set the domain to "djangojs" like `-d djangojs` for handlebars templates!')
-
-    # DJANGO_CHANGE(cpauya):
-    # Check handlebars extension are processed like a Django template but saved in `djangojs` domain.
-    if domain == 'djangojs' and is_file_ext_in_extensions and not is_handlebars:
+    if domain == 'djangojs' and file_ext in extensions:
         is_templatized = True
         orig_file = os.path.join(dirpath, file)
         with open(orig_file) as fp:
@@ -169,14 +153,10 @@ def process_file(file, dirpath, potfile, domain, verbosity,
             '--keyword=pgettext:1c,2 --keyword=npgettext:1c,2,3 '
             '--from-code UTF-8 --add-comments=Translators -o - "%s"' %
             (domain, wrap, location, work_file))
-    # DJANGO_CHANGE(cpauya):
-    # Check handlebars extension are processed like a Django template but saved in `djangojs` domain.
-    elif (domain == 'django' and (file_ext == '.py' or is_file_ext_in_extensions) and not is_handlebars) or \
-            (domain == 'djangojs' and is_handlebars):
+    elif domain == 'django' and (file_ext == '.py' or file_ext in extensions):
         thefile = file
         orig_file = os.path.join(dirpath, file)
-        # DJANGO_CHANGE(cpauya):
-        is_templatized = is_file_ext_in_extensions
+        is_templatized = file_ext in extensions
         if is_templatized:
             with open(orig_file, "rU") as fp:
                 src_data = fp.read()
@@ -362,8 +342,6 @@ def make_messages(locale=None, domain='django', verbosity=1, all=False,


 class Command(NoArgsCommand):
-    # DJANGO_CHANGE(cpauya):
-    # Include the handlebars extension for `djangojs` domain.
     option_list = NoArgsCommand.option_list + (
         make_option('--locale', '-l', default=None, dest='locale',
             help='Creates or updates the message files for the given locale (e.g. pt_BR).'),
@@ -372,7 +350,7 @@ class Command(NoArgsCommand):
         make_option('--all', '-a', action='store_true', dest='all',
             default=False, help='Updates the message files for all existing locales.'),
         make_option('--extension', '-e', dest='extensions',
-            help='The file extension(s) to examine (default: "html,txt", or "js,handlebars" if the domain is "djangojs"). Separate multiple extensions with commas, or use -e multiple times.',
+            help='The file extension(s) to examine (default: "html,txt", or "js" if the domain is "djangojs"). Separate multiple extensions with commas, or use -e multiple times.',
             action='append'),
         make_option('--symlinks', '-s', action='store_true', dest='symlinks',
             default=False, help='Follows symlinks to directories when examining source code and templates for translation strings.'),
@@ -411,9 +389,7 @@ class Command(NoArgsCommand):
         no_location = options.get('no_location')
         no_obsolete = options.get('no_obsolete')
         if domain == 'djangojs':
-            # DJANGO_CHANGE(cpauya):
-            # Include the handlebars extension for `djangojs` domain.
-            exts = extensions if extensions else ['js', 'handlebars']
+            exts = extensions if extensions else ['js']
         else:
             exts = extensions if extensions else ['html', 'txt']
         extensions = handle_extensions(exts)
diff --git a/python-packages/django/utils/translation/trans_real.py b/python-packages/django/utils/translation/trans_real.py
index 6ffe018..9c6ec43 100644
--- a/python-packages/django/utils/translation/trans_real.py
+++ b/python-packages/django/utils/translation/trans_real.py
@@ -471,9 +471,6 @@ block_re = re.compile(r"""^\s*blocktrans(\s+.*context\s+((?:"[^"]*?")|(?:'[^']*?
 endblock_re = re.compile(r"""^\s*endblocktrans$""")
 plural_re = re.compile(r"""^\s*plural$""")
 constant_re = re.compile(r"""_\(((?:".*?")|(?:'.*?'))\)""")
-# DJANGO_CHANGE(cpauya):
-# For handlebars templates using `{{_ "text here" }}`.
-constant_hb_re = re.compile(r"""^_\s((?:".*?")|(?:'.*?'))$""")
 one_percent_re = re.compile(r"""(?<!%)%(?!%)""")


@@ -561,9 +558,6 @@ def templatize(src, origin=None):
                 imatch = inline_re.match(t.contents)
                 bmatch = block_re.match(t.contents)
                 cmatches = constant_re.findall(t.contents)
-                # DJANGO_CHANGE(cpauya):
-                # For handlebars templates using `{{_ "text here" }}`.
-                hbmatches = constant_hb_re.findall(t.contents)
                 if imatch:
                     g = imatch.group(1)
                     if g[0] == '"':
@@ -586,10 +580,6 @@ def templatize(src, origin=None):
                 elif bmatch:
                     for fmatch in constant_re.findall(t.contents):
                         out.write(' _(%s) ' % fmatch)
-                    # DJANGO_CHANGE(cpauya):
-                    # For handlebars templates using `{{_ "text here" }}`.
-                    for hbmatch in constant_hb_re.findall(t.contents):
-                        out.write(' _(%s) ' % hbmatch)
                     if bmatch.group(1):
                         # A context is provided
                         context_match = context_re.match(bmatch.group(1))
@@ -605,11 +595,6 @@ def templatize(src, origin=None):
                 elif cmatches:
                     for cmatch in cmatches:
                         out.write(' _(%s) ' % cmatch)
-                # DJANGO_CHANGE(cpauya):
-                # For handlebars templates using `{{_ "text here" }}`.
-                elif hbmatches:
-                    for hbmatch in hbmatches:
-                        out.write(' _(%s) ' % hbmatch)
                 elif t.contents == 'comment':
                     incomment = True
                 else:
@@ -619,11 +604,6 @@ def templatize(src, origin=None):
                 cmatch = constant_re.match(parts[0])
                 if cmatch:
                     out.write(' _(%s) ' % cmatch.group(1))
-                # DJANGO_CHANGE(cpauya):
-                # For handlebars templates using `{{_ "text here" }}`.
-                hbmatch = constant_hb_re.match(parts[0])
-                if hbmatch:
-                    out.write(' _(%s) ' % hbmatch.group(1))
                 for p in parts[1:]:
                     if p.find(':_(') >= 0:
                         out.write(' %s ' % p.split(':',1)[1])
## END(djallado)


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
