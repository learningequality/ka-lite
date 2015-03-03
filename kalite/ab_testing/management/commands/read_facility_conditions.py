import csv
import json
import os

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    requires_model_validation = False

    def handle(self, *args, **options):

        assert len(args) == 1, "There must be exactly one argument, the csv of with the facility to condition mapping to add"

        csvfile = args[0]
        if not os.path.exists(csvfile):
            raise CommandError("CSV file %s should exist!" % csvfile)

        with open(csvfile) as f:
            # iterfile = iter(f.readline, "")
            reader = csv.DictReader(f, delimiter="\t")

            facility_grade_mappings = {}

            for row in reader:
                id = row["facility_id"]
                facility_grade_mappings[id] = row["grade"]

        savedir = os.path.join(os.path.dirname(__file__),
                               "..",
                               "..",
                               "data"
        )


        facility_grade_mappings_file = os.path.join(
            savedir,
            "facility_grade_mappings.json"
        )

        with open(facility_grade_mappings_file, "w") as f:
            json.dump(facility_grade_mappings, f,
                      sort_keys=True,
                      indent=4)
