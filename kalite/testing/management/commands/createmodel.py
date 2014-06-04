# Creates a model based on the specified input model name and json data.
# Exit with a zero value if everything goes alright. Otherwise will exit with a non-zero value (1).

import sys
import importlib
import json 

from optparse import make_option
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    args = "<data_model_name>"

    help = "Creates a model based on the specified input model name and json data."

    option_list = BaseCommand.option_list + (
        make_option('-d', '--data',
            action='store',
            dest='json_data',
            default=None,
            help='The json string representing the fields of the data model.'),
    )

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("No args specified")
        else:
            if not options["json_data"]:
                raise CommandError("Please specifiy input data as a json string")
            
            try:
                # Loading the model
                module_path, model_name = args[0].rsplit(".", 1)
                module = importlib.import_module(module_path)
                Model = getattr(module, model_name)

                # Reading the json data string into a map
                data_map = json.loads(options["json_data"])

                # Constructing an entity from the Model
                entity = Model(**data_map)
                entity.save()
                
                # Printing out the id of the entity
                sys.stdout.write("%s\n" % (entity.id))
                sys.exit(0)
            except:
                # In case of an error just exit with a non-zero value
                sys.exit(1)
