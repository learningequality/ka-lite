import importlib
from optparse import make_option
from . import resolve_model

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
            model = resolve_model(args[0])

            model_id = options["id"]
            data = model.objects.get(pk=model_id)
            logging.info("Retrieved '%s' entry with primary key: '%s'" % (args[0], model_id))

            serialized_data = serializers.serialize("json", [data])
            logging.debug("Serialized data: '%s'" % serialized_data)
            return serialized_data
        else:
            raise Exception("Please specify --id to fetch model.")
