# Creates a model based on the specified input model name and json data.
# Exit with a zero value if everything goes alright. Otherwise will exit with a non-zero value (1).

import sys
import json

from optparse import make_option
from fle_utils.importing import resolve_model

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
        make_option('-c', '--count',
            action='store',
            dest='count',
            default=1,
            help='The number of instances to create.'),
    )

    def handle(self, *args, **options):

        if len(args) != 1:
            raise CommandError("No args specified")
        else:
            if not options["json_data"]:
                raise CommandError("Please specify input data as a json string")

            try:
                model = resolve_model(args[0])

                # Reading the json data string into a map
                data_map = json.loads(options["json_data"])

                entity_ids = []

                for i in range(int(options["count"])):

                    # Incorporate the iteration number into any fields that need it
                    model_data = {}
                    for key, val in data_map.items():
                        if "%d" in val or "%s" in val:
                            val = val % i
                        model_data[key] = val

                    # Constructing an entity from the Model
                    entity = model(**model_data)
                    entity.full_clean()
                    entity.save()

                    entity_ids.append(entity.id)

                # Printing out the id of the entity
                sys.stdout.write("%s\n" % (",".join(entity_ids)))
                sys.exit(0)
            except:
                raise
