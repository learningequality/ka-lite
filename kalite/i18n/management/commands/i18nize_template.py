import glob
import logging
import os
import subprocess

from optparse import make_option
from django.core.management.base import BaseCommand, CommandError


def django_module(app_name, parse_paths, i18nize_file):
    """
    Parse the django_app templates and its handlebars templates
    """
    # parse hbtemplates, handlebars
    if parse_paths is not None:
        for path in parse_paths:
            if path == "hbtemplates":
                for root, dirs, files in os.walk(app_name):
                    for file in files:
                        if file.endswith(".handlebars"):
                            file_path = os.path.join(root, file)
                            subprocess.call("i18nize-templates %s" % (file_path), shell=True)

            else:
                for root, dirs, files in os.walk(app_name):
                    for file in files:
                        if file.endswith(".html"):
                            file_path = os.path.join(root, file)
                            subprocess.call("i18nize-templates %s" % (file_path), shell=True)
    else:
    # Find a specific file to i18nize
    # for filename in fnmatch.filter(files, pattern)
        for root, dirs, files in os.walk(app_name):
            for file in files:
                if file == i18nize_file[0]:
                    file_path = os.path.join(root, file)
                    subprocess.call("i18nize-templates %s" % (file_path), shell=True)


class Command(BaseCommand):
    """
    This management command ask the module that will be i18nize.
    this cover the handlebars template and the templates
    converting to recognizable expression by our i18n.
    Feature implemented:
        parse by django app
        parse by django app and specific file type
        parse by django app and specific file.
    usage :
        sample usage
            python manage.py i18nize-templates coachreports
            python manage.py i18nize-templates coachreports -parse templates
            python manage.py i18nize-templates coachreports -parse hbtemplates
            python manage.py i18nize_template  coachreports --parse-file facility-select.handlebars
    """
    option_list = BaseCommand.option_list + (
       make_option('--parse',
            action='append',
            dest="parse",
            help='Select a file extention to be parse e.g(handlebars or html)'),

        make_option('--parse-file',
            action='append',
            dest="parse_file",
            help='Select a specific file extention to be parse e.g(handlebars or html)'),
    )

    def handle(self, *args, **options):
        extension_option = options.get("parse")
        i18nize_file = options.get("parse_file")
        parse_file = ["hbtemplates", "templates"]
        parse_flag = True
        if extension_option is not None:
            if extension_option[0] in parse_file:
                parse_file = extension_option
            else:
                parse_flag = False

        if parse_flag is True:
            for django_app in args:
                if i18nize_file is not None:
                    parse_file = None
                try:
                    self.stdout.write(">>> i18nize hbtemplate and templates")
                    django_module(app_name=django_app, parse_paths=parse_file, i18nize_file=i18nize_file)
                    self.stdout.write(">>> i18nize hbtemplate and templates done in %s" % (django_app))

                except:
                    self.stdout.write("It seems you didn't have the tools for i18nze-templates"
                                      "Fork this tools to https://github.com/mrpau/i18nize_templates "
                                      "Install then setup.py to use this tool")
        else:
            self.stdout.write("The file type specified is not available for i18nize.Did you miss type this?")