import json
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from fle_utils.importing import resolve_model


class Command(BaseCommand):
    args = "<data_model_name> <model_id>"

    help = "Modifies an existing model with the given json data"

    option_list = BaseCommand.option_list + (
        make_option('-d', '--data',
                    action='store',
                    dest='json_data',
                    default=None,
                    help='The json string representing the fields of the data model.'),
    )

    def handle(self, *args, **kwargs):
        if len(args) != 2:
            raise CommandError("Wrong number of args specified")

        model_class = resolve_model(args[0])
        model_id = args[1]
        newdata = json.loads(kwargs['json_data'])

        model = model_class.objects.get(id=model_id)

        for attr, value in newdata.iteritems():
            setattr(model, attr, value)

        model.save()
