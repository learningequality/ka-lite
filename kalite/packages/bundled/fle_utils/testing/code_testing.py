import copy
import glob
import importlib
import os
import re

from django.conf import settings; logging = settings.LOG
from django.utils import unittest


def get_module_files(module_dirpath, file_filter_fn):
    source_files = []
    for root, dirs, files in os.walk(module_dirpath):  # Recurse over all files
        source_files += [os.path.join(root, f) for f in files if file_filter_fn(f)]  # Filter py files
    return source_files

class FLECodeTest(unittest.TestCase):
    testable_packages = []

    def __init__(self, *args, **kwargs):
        """ """
        super(FLECodeTest, self).__init__(*args, **kwargs)
        if not hasattr(self.__class__, 'our_apps'):
            self.__class__.our_apps = set([app for app in settings.INSTALLED_APPS if app in self.testable_packages or app.split('.')[0] in self.testable_packages])
            self.__class__.compute_app_dependencies()
            self.__class__.compute_app_urlpatterns()

    @classmethod
    def compute_app_dependencies(cls):
        """For each app in settings.INSTALLED_APPS, load that app's settings.py to grab its dependencies
        from its own INSTALLED_APPS.

        Note: assumes cls.our_apps has already been computed.
        """
        cls.our_app_dependencies = {}

        # Get each app's dependencies.
        for app in cls.our_apps:
            module = importlib.import_module(app)
            module_dirpath = os.path.dirname(module.__file__)
            settings_filepath = os.path.join(module_dirpath, 'settings.py')

            if not os.path.exists(settings_filepath):
                our_app_dependencies = []
            else:
                # Load the settings.py file.  This requires settings some (expected) global variables,
                #   such as PROJECT_PATH and ROOT_DATA_PATH, such that the scripts execute stand-alone
                # TODO: make these scripts execute stand-alone.
                global_vars = copy.copy(globals())
                global_vars.update({
                    "__file__": settings_filepath,  # must let the app's settings file be set to that file!
                    'PROJECT_PATH': settings.PROJECT_PATH,
                    'ROOT_DATA_PATH': getattr(settings, 'ROOT_DATA_PATH', os.path.join(settings.PROJECT_PATH, 'data')),
                })
                app_settings = {'__package__': app}  # explicit setting of the __package__, to allow absolute package ref'ing
                execfile(settings_filepath, global_vars, app_settings)
                our_app_dependencies = [anapp for anapp in app_settings.get('INSTALLED_APPS', []) if anapp in cls.our_apps]

            cls.our_app_dependencies[app] = our_app_dependencies


    @classmethod
    def get_fle_imports(cls, app):
        """Recurses over files within an app, searches each file for KA Lite-relevant imports,
        then grabs the fully-qualified module import for each import on each line.

        The logic is hacky and makes assumptions (no multi-line imports, but handles comma-delimited import lists),
        but generally works.

        Returns a dict of tuples
            key: filepath
            value: (actual code line, reconstructed import)
        """
        module = importlib.import_module(app)
        module_dirpath = os.path.dirname(module.__file__)

        imports = {}

        py_files = get_module_files(module_dirpath, lambda f: os.path.splitext(f)[-1] in ['.py'])
        for filepath in py_files:
            lines = open(filepath, 'r').readlines()  # Read the entire file
            import_lines = [l.strip() for l in lines if 'import' in l]  # Grab lines containing 'import'
            our_import_lines = []
            for import_line in import_lines:
                for rexp in [r'^\s*from\s+(.*)\s+import\s+(.*)\s*$', r'^\s*import\s+(.*)\s*$']: # Match 'import X' and 'from A import B' syntaxes
                    matches = re.match(rexp, import_line)
                    groups = matches and list(matches.groups()) or []
                    import_mod = []
                    for list_item in ((groups and groups[-1].split(",")) or []):  # Takes the last item (which get split into a CSV list)
                        cur_item = '.'.join([item.strip() for item in (groups[0:-1] + [list_item])])  # Reconstitute to fully-qualified import
                        if any([a for a in cls.our_apps if a in cur_item]):  # Search for the app in all the apps we know matter
                            our_import_lines.append((import_line, cur_item))  # Store line and import item as a tuple
                            if app in cur_item:  # Special case: warn if fully qualified import within an app (should be relative)
                                logging.warn("*** Please use relative imports within an app (%s: found '%s')" % (app, import_line))
                        else:  # Not a relevant / tracked import
                            logging.debug("*** Skipping import: %s (%s)" % (import_line, cur_item))
            imports[filepath] = our_import_lines
        return imports

    # @unittest.skipIf(settings.RUNNING_IN_TRAVIS, "Skipping import tests until we get them all passing locally.")
    # def test_imports(self):
    #     """For each installed app, gets all FLE imports within the code.
    #     Then checks intended dependencies (via the app's settings.py:INSTALLED_APPS)
    #     and looks for differences.

    #     A single assert is done after recursing (and accumulating errors) over all apps.
    #     """

    #     bad_imports = {}
    #     for app, app_dependencies in self.our_app_dependencies.iteritems():
    #         imports = self.__class__.get_fle_imports(app)

    #         # Don't include [app] in search; we want all such imports to be relative.
    #         bad_imports[app] = [str((f, i[0])) for f, ins in imports.iteritems() for i in ins if not any([a for a in app_dependencies if a in i[1]])]

    #     # Join the bad imports together into a user-meaningful string.
    #     bad_imports_text = "\n\n".join(["%s:\n%s\n%s" % (app, "\n".join(self.our_app_dependencies[app]), "\n".join(bad_imports[app])) for app in bad_imports if bad_imports[app]])
    #     self.assertFalse(any([app for app, bi in bad_imports.iteritems() if bi]), "Found unreported app dependencies in imports:\n%s" % bad_imports_text)


    @classmethod
    def compute_app_urlpatterns(cls):
        """For each app in settings.INSTALLED_APPS, load that app's *urls.py to grab its
        defined URLS.

        Note: assumes cls.our_apps has already been computed.
        """
        cls.app_urlpatterns = {}

        # Get each app's dependencies.
        for app in cls.our_apps:
            module = importlib.import_module(app)
            module_dirpath = os.path.dirname(module.__file__)
            settings_filepath = os.path.join(module_dirpath, 'settings.py')

            urlpatterns = []
            source_files = get_module_files(module_dirpath, lambda f: 'urls' in f and os.path.splitext(f)[-1] in ['.py'])
            for filepath in source_files:
                fq_urlconf_module = app + os.path.splitext(filepath[len(module_dirpath):])[0].replace('/', '.')

                logging.info('Processing urls file: %s' % fq_urlconf_module)
                mod = importlib.import_module(fq_urlconf_module)
                urlpatterns += mod.urlpatterns

            cls.app_urlpatterns[app] = urlpatterns


    @classmethod
    def get_url_reversals(cls, app):
        """Recurses over files within an app, searches each file for KA Lite-relevant URL confs,
        then grabs the fully-qualified module import for each import on each line.

        The logic is hacky and makes assumptions (no multi-line imports, but handles comma-delimited import lists),
        but generally works.

        Returns a dict of tuples
            key: filepath
            value: (actual code line, reconstructed import)
        """

        module = importlib.import_module(app)
        module_dirpath = os.path.dirname(module.__file__)

        url_reversals = {}

        source_files = get_module_files(module_dirpath, lambda f: os.path.splitext(f)[-1] in ['.py', '.html'])
        for filepath in source_files:
            mod_revs = []
            for line in open(filepath, 'r').readlines():
                new_revs = []
                for rexp in [r""".*reverse\(\s*['"]([^\)\s,]+)['"].*""", r""".*\{%\s*url\s+['"]([^%\s]+)['"].*"""]: # Match 'reverse(URI)' and '{% url URI %}' syntaxes

                    matches = re.match(rexp, line)
                    groups = matches and list(matches.groups()) or []
                    if groups:
                        new_revs += groups
                        logging.debug('Found: %s; %s' % (filepath, line))

                if not new_revs and ('reverse(' in line or '{% url' in line):
                    logging.debug("\tSkip: %s; %s" % (filepath, line))
                mod_revs += new_revs

            url_reversals[filepath] = mod_revs
        return url_reversals


    @classmethod
    def get_url_modules(cls, url_name):
        """Given a URL name, returns all INSTALLED_APPS that have that URL name defined within the app."""

        # Search patterns across all known apps that are named have that name.
        found_modules = [app for app, pats in cls.app_urlpatterns.iteritems() for pat in pats if getattr(pat, "name", None) == url_name]
        return found_modules

    # @unittest.skipIf(settings.RUNNING_IN_TRAVIS, "Skipping import tests until we get them all passing locally.")
    # def test_url_reversals(self):
    #     """Finds all URL reversals that aren't found within the defined INSTALLED_APPS dependencies"""
    #     bad_reversals = {}

    #     for app, app_dependencies in self.our_app_dependencies.iteritems():
    #         url_names_by_file = self.__class__.get_url_reversals(app)
    #         url_names = [pat for pat_list in url_names_by_file.values() for pat in pat_list]  # Flatten into list (not per-file)

    #         # Clean names
    #         url_names = [n for n in url_names if n and not n.startswith('admin:')]  # Don't deal with admin URLs.
    #         url_names = [n for n in url_names if n and not '.' in n]  # eliminate fully-qualified url names
    #         url_names = set(url_names)  # Eliminate duplicates

    #         # for each referenced url name, make sure this app defin
    #         bad_reversals[app] = []
    #         for url_name in url_names:
    #             referenced_modules = set(self.get_url_modules(url_name))
    #             if not referenced_modules.intersection(set([app] + app_dependencies)):
    #                 bad_reversals[app].append((url_name, list(referenced_modules)))

    #     bad_reversals_text = "\n\n".join(["%s: unexpected dependencies found!\n\t(url_name [module that defines url_name])\n\t%s\nExpected dependencies:\n\t%s" % (
    #         app,
    #         "\n\t".join([str(t) for t in bad_reversals[app]]),
    #         "\n\t".join(self.our_app_dependencies[app]),
    #     ) for app in bad_reversals if bad_reversals[app]])
    #     self.assertFalse(any([app for app, bi in bad_reversals.iteritems() if bi]), "Found unreported app dependencies in URL reversals:\n%s" % bad_reversals_text)

