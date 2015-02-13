import logging
import os
import subprocess

from django.conf import settings; logging = settings.LOG
from django.core.management.base import AppCommand
from django.core.management.commands.makemessages import handle_extensions

from optparse import make_option


def i18nize_parser(parse_dir, extensions, parse_file, ignores):
    """
    Call the `i18nize-templates` script which will parse the
    files with the extensions specified.
    """
    filenames_to_process = []
    for dirpath, dirnames, filenames in os.walk(parse_dir):
        logging.info("==> Looking for template file/s at %s" % dirpath)
        for filename in filenames:
            full_filename = os.path.join(dirpath, filename)
            # Validate if it's part of our ignores
            if is_ignored(full_filename, ignores):
                continue

            # Validate file extensions.
            for extension in extensions:
                if filename.endswith(extension):
                    # Since `single_file` is not in full path, there's a possibility that
                    # we will find files of the same name in one app, so we just loop thru
                    # all files to find the duplicates.
                    file_path = os.path.join(dirpath, filename)
                    if parse_file:
                        if not file_path.endswith(parse_file):
                            continue
                        else:
                            logging.info("==> Processing single template file %s..." % parse_file)
                    filenames_to_process.append(file_path)
    if filenames_to_process:
        # MUST: Instead of passing the filenames one by one, we join them into a
        # single string separated by space and pass it as an argument to the
        # `i18nize-templates` script.
        logging.info("Found %s template/s to process..." % (len(filenames_to_process),))
        logging.info("Calling `i18nize-templates`...")
        filenames = ' '.join(filenames_to_process)
        subprocess.call("i18nize-templates %s" % (filenames,), shell=True)
        logging.info("DONE processing.")
    else:
        logging.info('Did not find any files with extensions [%s] to process!' % (", ".join(extensions),))


def is_ignored(filepath, ignores):
    """
    Check to see if one of the elements in ignores is part of the filepath.
    """
    for ignore in ignores:
        if ignore in filepath:
            return True
    else:
        return False


class Command(AppCommand):
    """
    This management command will i18nize the Django and Handlebars templates with the following.
        * Django templates == {% trans "text here" %}
        * Handlebars templates == {{_ "text here" }}

    Features implemented:
        * Parse by django app.
        * Parse by django app and specific files by extensions, defaults to [".html", ".handlebars"].
        * Parse by django app and specific file.  Example: "base.html"
        * Parse by django app and specifically formatted file.  Example "admin/base.html"

    Example Usages:
        python manage.py i18nize_templates coachreports
        python manage.py i18nize_templates coachreports -e html
        python manage.py i18nize_templates coachreports --extension=html,handlebars

        # May find multiple `base.html` files in the `distributed` app.
        python manage.py i18nize_templates distributed --parse-file=base.html

        # This will look only for specific `admin/base.html` inside the `distributed` app.
        python manage.py i18nize_templates distributed --parse-file=admin/base.html
    """
    option_list = AppCommand.option_list + (
        make_option('--extension', '-e', dest='extensions',
                    action='append', default=[],
                    help='The file extension(s) to render (default:"html,handlebars"). '
                         'Separate multiple extensions with commas, or use '
                         '-e multiple times.'),

        make_option('--ignore', '-i', dest='ignores',
                    action='append', default=[],
                    help="Comma-separated values that if present in a template's full pathname will cause that template to be ignored."),

        make_option('--parse-file', action='append', dest="parse_file",
                    help='Select a specific file to be parsed, put only the filename and not the full path.'),
    )
    help = ("Parse the specified template or handlebars to be i18nized.")

    def handle_app(self, app, **options):
        extensions_option = options.get('extensions')
        if not extensions_option:
            # Default to process [".html", ".handlebars"] if extensions are not specified.
            extensions_option = ['html', 'handlebars']
        extensions = tuple(handle_extensions(extensions_option, ignored=()))
        parse_file = options.get("parse_file")
        ignores = options.get("ignores")
        if parse_file and isinstance(parse_file, list):
            parse_file = parse_file[0]

        # TODO(cpauya): Get the app name here.
        if parse_file:
            logging.info("Will look for %s only at %s app with extensions: [%s]..." %
                        (parse_file, app.__file__, ', '.join(extensions),))
        else:
            logging.info("Will look for template files at %s app with extensions: [%s]..." %
                        (app.__name__, ', '.join(extensions)))

        local_dir = os.path.dirname(app.__file__)
        i18nize_parser(parse_dir=local_dir, extensions=extensions, parse_file=parse_file, ignores=ignores)
