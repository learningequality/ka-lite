import importlib
from optparse import make_option

from django.conf import settings; logging = settings.LOG
from django.core.management.base import BaseCommand, CommandError
from django.core import serializers

class Command(BaseCommand):
    args = "<module_path>"

    help = "Reads model data and returns it."

    option_list = BaseCommand.option_list + (
        make_option('-i', '--id',
            action='store',
            type='string',
            dest='id',
            help='Id of the model object to read'),
    )

    def handle(self, *args, **options):
        if (len(args) == 0):
            raise Exception("Please specify model class name.")

        if options["id"]:
            module_path, model_name = args[0].rsplit(".", 1)
            module = importlib.import_module(module_path)
            model = getattr(module, model_name)

            model_id = options["id"]
            data = model.objects.get(pk=model_id)
            logging.info("Retrieved '%s' entry with primary key: '%s'" % (model_name, model_id))

            serialized_data = serializers.serialize("json", [data])
            logging.debug("Serialized data: '%s'" % serialized_data)
            return serialized_data
        else:
            raise Exception("Please specify --id to fetch model.")
