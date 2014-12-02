import glob
import logging
import os
import subprocess

from optparse import make_option
from django.core.management.base import BaseCommand, CommandError


def django_module(app_name, parse_paths):
    """
    Parse the django_app templates and its handlebars templates
    """
    for path in parse_paths:
        local_dir = os.path.abspath(os.path.join(app_name, path))
        file_dir = glob.glob('%s/*' % (local_dir))
        if path == "hbtemplates":
            for file_path in file_dir:
                subprocess.call("i18nize-templates %s/*.handlebars" % (file_path), shell=True)

        else:
            for file_path in file_dir:
                subprocess.call("i18nize-templates %s/*.html" % (file_path), shell=True)


class Command(BaseCommand):
    """
    This management command ask the module that will be i18nize.
    this cover the handlebars template and the templates
    converting to recognizable expression by our i18n.
    usage :
        python manage.py i18nize-templates <django_app>
        sample usage
            python manage.py i18nize-templates coachreports
            python manage.py i18nize-templates coachreports -parse templates
            python manage.py i18nize-templates coachreports -parse hbtemplates
    """
    option_list = BaseCommand.option_list + (
       make_option('--parse',
            action='append',
            dest="parse",
            help='Select a file extention to be parse e.g(handlebars or html)'),
    )

    def handle(self, *args, **options):
        extension_option = options.get("parse")
        parse_file = ["hbtemplates", "templates"]
        parse_flag = True
        if extension_option is not None:
            if extension_option[0] in parse_file:
                parse_file = extension_option
            else:
                parse_flag = False

        if parse_flag is True:
            for django_app in args:
                try:
                    self.stdout.write(">>> i18nize hbtemplate and templates")
                    django_module(app_name=django_app, parse_paths=parse_file)
                    self.stdout.write(">>> i18nize hbtemplate and templates done in %s" % (django_app))

                except:
                    self.stdout.write("It seems you didn't have the tools for i18nze-templates"
                                      "Fork this tools to https://github.com/mrpau/i18nize_templates "
                                      "Install then setup.py to use this tool")
        else:
            self.stdout.write("The file type specified is not available for i18nize.Did you miss type this?")