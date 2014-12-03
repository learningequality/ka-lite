import logging
import os
import subprocess

from django.core.management.base import AppCommand
from django.core.exceptions import ValidationError
from optparse import make_option
logger = logging.getLogger(__name__)

def i18nize_parser(parse_dir, parse_exts, i18nize_file):
    """
    Parse the django_app templates and its handlebars templates
    """
    for root, dirs, files in os.walk(parse_dir):
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
            python manage.py i18nize_templates coachreports
            python manage.py i18nize_templates coachreports --parse templates
            python manage.py i18nize_templates coachreports --parse hbtemplates
            python manage.py i18nize_templates coachreports --parse-file facility-select.handlebars
    """
    option_list = AppCommand.option_list + (
        make_option('--parse', action='append', dest="parse",
                    help='Select a file extension to be parse e.g(handlebars or html)'),

        make_option('--parse-file', action='append', dest="parse_file",
                    help='Select a specific file to be parse'),
    )
    help = ("Parse the specified template or handlebars to be i18n")

    def handle_app(self, app, **options):
        extension_option = options.get("parse")
        i18nize_file = options.get("parse_file")
        parse_file = ["hbtemplates", "templates"]
        exts = handle_extensions()
        local_dir = os.path.dirname(app.__file__)
        if extension_option is not None:
            if extension_option[0] in parse_file:
                exts = handle_extensions(parse_file=extension_option[0])
            else:
                raise ValidationError("The %s is not a valid file type" % (extension_option[0]))

        logger.info(">>> i18nize hbtemplate and templates")
        i18nize_parser(parse_dir=local_dir, parse_exts=exts, i18nize_file=i18nize_file)