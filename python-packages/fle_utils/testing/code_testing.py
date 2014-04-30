import copy
import glob
import importlib
import os
import re

from django.conf import settings; logging = settings.LOG
from django.utils import unittest


class FLECodeTest(unittest.TestCase):
    testable_packages = []

    def __init__(self, *args, **kwargs):
        """ """
        super(FLECodeTest, self).__init__(*args, **kwargs)
        if not hasattr(self.__class__, 'our_apps'):
            self.__class__.set_app_dependencies()

    @classmethod
    def set_app_dependencies(cls):

        cls.our_apps = set([app for app in settings.INSTALLED_APPS if app in cls.testable_packages or app.split('.')[0] in cls.testable_packages])
        cls.our_app_dependencies = {}

        # Get each app's dependencies.
        for app in cls.our_apps:
            module = importlib.import_module(app)
            module_dirpath = os.path.dirname(module.__file__)
            settings_filepath = os.path.join(module_dirpath, 'settings.py')

            if not os.path.exists(settings_filepath):
                our_app_dependencies = []
            else:
                app_settings = {'__package__': app}  # explicit setting of the __package__, to allow absolute package ref'ing
                global_vars = copy.copy(globals())
                global_vars.update({
                    "__file__": settings_filepath,  # must let the app's settings file be set to that file!
                    'PROJECT_PATH': settings.PROJECT_PATH,
                    'ROOT_DATA_PATH': getattr(settings, 'ROOT_DATA_PATH', os.path.join(settings.PROJECT_PATH, 'data')),
                })
                execfile(settings_filepath, global_vars, app_settings)
                our_app_dependencies = [anapp for anapp in app_settings.get('INSTALLED_APPS', []) if anapp in cls.our_apps]

            cls.our_app_dependencies[app] = our_app_dependencies

    @classmethod
    def get_imports(cls, app):
        module = importlib.import_module(app)
        module_dirpath = os.path.dirname(module.__file__)

        imports = {}

        for root, dirs, files in os.walk(module_dirpath):
            py_files = [f for f in files if os.path.splitext(f)[-1] == '.py']
            for py_file in py_files:
                filepath = os.path.join(root, py_file)

                lines = open(filepath, 'r').readlines()
                import_lines = [l.strip() for l in lines if 'import' in l]
                our_import_lines = []
                for import_line in import_lines:
                    for rexp in [r'^\s*from\s+(.*)\s+import\s+(.*)\s*$', r'^\s*import\s+(.*)\s*$']:
                        matches = re.match(rexp, import_line)
                        groups = matches and list(matches.groups()) or []
                        import_mod = []
                        for list_item in ((groups and groups[-1].split(",")) or []):
                            cur_item = '.'.join([item.strip() for item in (groups[0:-1] + [list_item])])
                            if any([a for a in cls.our_apps if a in cur_item]):
                                our_import_lines.append((import_line, cur_item))
                                if app in cur_item:
                                    logging.warn("*** Please use relative imports within an app (%s: found '%s')" % (app, import_line))
                            else:
                                logging.debug("*** Skipping import: %s (%s)" % (import_line, cur_item))
                imports[filepath] = our_import_lines
        return imports

    def test_imports(self):
        bad_imports = {}
        for app, app_dependencies in self.our_app_dependencies.iteritems():
            imports = self.__class__.get_imports(app)
            # Don't include [app] in search; we want all such imports to be relative.
            bad_imports[app] = [str((f, i[0])) for f, ins in imports.iteritems() for i in ins if not any([a for a in app_dependencies if a in i[1]])]

        bad_imports_text = "\n\n".join(["%s:\n%s\n%s" % (app, "\n".join(self.our_app_dependencies[app]), "\n".join(bad_imports[app])) for app in bad_imports if bad_imports[app]])
        self.assertFalse(any([app for app, bi in bad_imports.iteritems() if bi]), "Found unreported app dependencies in imports:\n%s" % bad_imports_text)


    def test_url_reversals(self):
        pass#import pdb; pdb.set_trace()

