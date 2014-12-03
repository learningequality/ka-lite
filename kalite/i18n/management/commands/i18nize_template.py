import glob
import logging
import os
import subprocess

from optparse import make_option
from django.core.management.base import AppCommand

# logger = getLogger('management_commands')


def i18nize_parser(app_name, parse_exts, i18nize_file):
    """
    Parse the django_app templates and its handlebars templates
    """
    # parse hbtemplates, handlebars
    for root, dirs, files in os.walk(app_name):
        for file in files:
            if i18nize_file is not None:
                if file == i18nize_file[0]:
                    file_path = os.path.join(root, file)
                    subprocess.call("i18nize-templates %s" % (file_path), shell=True)
            else:
                for file_exts in parse_exts:
                    if file.endswith(file_exts):
                        file_path = os.path.join(root, file)
                        subprocess.call("i18nize-templates %s" % (file_path), shell=True)


def handle_extensions(parse_file=None):
    exts = [".handlebars", ".html"]
    if parse_file == "hbtemplates":
        exts = [".handlebars"]
    if parse_file == "templates":
        exts = [".html"]
    return exts


class Command(AppCommand):
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
            python manage.py i18nize_template coachreports
            python manage.py i18nize_template coachreports --parse templates
            python manage.py i18nize_template coachreports --parse hbtemplates
            python manage.py i18nize_template coachreports --parse-file facility-select.handlebars
    """
    option_list = AppCommand.option_list + (
       make_option('--parse',
            action='append',
            dest="parse",
            help='Select a file extention to be parse e.g(handlebars or html)'),

        make_option('--parse-file',
            action='append',
            dest="parse_file",
            help='Select a specific file extention to be parse e.g(handlebars or html)'),
    )
    help = ("Modify the specified template or handlebars to be i18n")

    def handle(self, *args, **options):
        extension_option = options.get("parse")
        i18nize_file = options.get("parse_file")
        parse_file = ["hbtemplates", "templates"]
        parse_flag = True
        exts = handle_extensions()
        if extension_option is not None:
            if extension_option[0] in parse_file:
                exts = handle_extensions(parse_file=extension_option[0])
            else:
                parse_flag = False

        if parse_flag is True:
            for django_app in args:

                try:
                    logging.warn(">>> i18nize hbtemplate and templates")
                    i18nize_parser(app_name=django_app, parse_exts=exts, i18nize_file=i18nize_file)
                    logging.warn(">>> i18nize hbtemplate and templates done in %s" % (django_app))

                except:
                    logging.warn("It seems you didn't have the tools for i18nze-templates"
                                      "Fork this tools to https://github.com/mrpau/i18nize_templates "
                                      "Install then setup.py to use this tool")
        else:
            logging.error("The file type specified is not available for i18nize.Did you miss type this?")