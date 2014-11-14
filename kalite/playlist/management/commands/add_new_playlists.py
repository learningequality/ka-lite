import json
import os
import shutil

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Add new playlists given in *playlists.json* arg to the current playlists.json"

    requires_model_validation = False

    def handle(self, *args, **options):

        assert len(args) == 1, "There must be exactly one argument, the playlists to add"

        pl_file = args[0]
        with open(pl_file) as f:
            new_playlists = json.load(f)
            new_playlists_dict = dict((pl["id"], pl) for pl in new_playlists)

        playlists_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "playlist",
        )                       # we hardcode so i don't have dependencies in the app

        old_pl_file = os.path.join(
            playlists_path,
            "playlists.json"
        )                       # we hardcode so i don't have dependencies in the app

        with open(old_pl_file) as f:
            old_playlists = json.load(f)
            old_playlists_dict = dict((pl["id"], pl) for pl in old_playlists)

        playlists_that_will_be_clobbered = (set(old_playlists_dict.keys()) &
                                            set(new_playlists_dict.keys()))

        print "You will clobber the playlists with the following IDs:"
        for pl in playlists_that_will_be_clobbered:
            print pl

        if raw_input("Are you sure you want to continue? (y/n)") == "y":
            # backup the old playlists json first
            backup_pl_file_path = os.path.join(playlists_path,
                                               "playlists.json.bak")
            shutil.move(old_pl_file, backup_pl_file_path)

            # overwrite the old pl file with the combined pl file
            combined_playlists_dict = old_playlists_dict.copy()

            # mark all the old playlists as show: False
            for k, v in combined_playlists_dict.iteritems():
                v['show'] = False

            combined_playlists_dict.update(new_playlists_dict)

            with open(old_pl_file, "w") as f:
                vals = sorted(combined_playlists_dict.values(),
                              key=lambda x: x["id"])
                json.dump(
                    vals,
                    f,
                    sort_keys=True,
                    indent=2,
                    separators=(",", ": ")
                )
