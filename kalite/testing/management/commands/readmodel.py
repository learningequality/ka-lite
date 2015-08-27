import datetime
import importlib
import json
import sys

from optparse import make_option
from fle_utils.importing import resolve_model

from django.conf import settings; logging = settings.LOG
from django.core.management.base import BaseCommand, CommandError
from django.core import serializers

dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None

class Command(BaseCommand):
    args = "<model_path>"

    help = "Reads model object with provided ID as primary key and returns it." \
        " The retuned data is in django serialized format similar to when a list of objects are serialized." \
        " If no data is found exit code '1' is returned."

    option_list = BaseCommand.option_list + (
        make_option('-i', '--id',
            action='store',
            type='string',
            dest='id',
            help='Primary key of the model object to read'),
    )

    def handle(self, *args, **options):
        if (len(args) == 0):
            raise CommandError("Please specify model class name.")

        model_path = args[0]
        model_id = options["id"]
        if model_id:
            Model = resolve_model(model_path)
            
            try:
                data = Model.objects.get(pk=model_id)
                # logging.info("Retrieved '%s' entry with primary key: '%s'" % (model_path, model_id))

                serialized_data = serializers.serialize("python", [data])[0]["fields"]
                serialized_data["id"] = model_id
                logging.debug("Serialized data: '%s'" % serialized_data)
                print json.dumps(serialized_data, default=dthandler)

            except Model.DoesNotExist:
                logging.error("Could not find '%s' entry with primary key: '%s'" % (model_path, model_id))
                sys.exit(1)
            
        else:
            raise CommandError("Please specify --id to fetch model.")
