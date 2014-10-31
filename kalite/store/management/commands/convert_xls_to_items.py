import json
import os
import shutil
import xlrd
from slugify import slugify

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Convert store items given in *.xls* arg to the current items.py"

    def handle(self, *args, **options):

        assert len(args) == 1, "There must be exactly one argument, the file to convert"

        # Open the xls file and select the first worksheet
        xls_file = xlrd.open_workbook(args[0])
        sh = xls_file.sheet_by_index(0)
 
        store_list = {
            "gift_card": {
            "returnable" : "False",
            "title" : "Gift Card",
            "description" : "Points rewarded for quizzes and tests",
            "shown" : "False",
        }
        }

        # Iterate through each row in worksheet and fetch values into dict
        for rownum in range(2, sh.nrows):
            row_values = sh.row_values(rownum)
            slug = slugify(row_values[0])
            if slug:
                item = {}
                item ["title"] = row_values[0]
                item["description"] = row_values[1]
                item["cost"] = row_values[2]
                item["thumbnail"] = row_values[3]
                item["resource_id"] =  ""
                item["resource_type"] =  ""
                item["shown"] =  "True"
                store_list[slug] = item

        # Serialize the dict of dicts to JSON
        data = "STORE_ITEMS = " + json.dumps(store_list, indent=4, separators=(",", ": "))

        items_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "data",
        )

        items_file = os.path.join(
            items_path,
            "items.py"
        )       
 
        if raw_input("Are you sure you want to continue? (y/n)") == "y":
            # backup the old index.py first
            backup_items_file_path = os.path.join(items_path, "items.py.bak")
            shutil.move(items_file, backup_items_file_path)

        # Write to file
        with open(items_file, "w") as f:
            f.write(data)

