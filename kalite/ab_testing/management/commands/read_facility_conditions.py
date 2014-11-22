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

            facility_unit_mappings = {}
            facility_grade_mappings = {}

            for row in reader:
                facility = {}
                facility["101"] = row["unit_1"]
                facility["102"] = row["unit_2"]
                facility["103"] = row["unit_3"]
                facility["104"] = row["unit_4"]

                id = row["facility_id"]
                facility_unit_mappings[id] = facility
                facility_grade_mappings[id] = row["grade"]

        savedir = os.path.join(os.path.dirname(__file__),
                               "..",
                               "..",
                               "data"
        )

        facility_unit_mappings_file = os.path.join(
            savedir,
            "facility_unit_mappings.json"
        )

        facility_grade_mappings_file = os.path.join(
            savedir,
            "facility_grade_mappings.json"
        )

        with open(facility_unit_mappings_file, "w") as f:
            json.dump(facility_unit_mappings, f,
                      sort_keys=True,
                      indent=4)

        with open(facility_grade_mappings_file, "w") as f:
            json.dump(facility_grade_mappings, f,
                      sort_keys=True,
                      indent=4)
