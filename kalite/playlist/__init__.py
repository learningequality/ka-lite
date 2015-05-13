import json
from pkg_resources import resource_filename

playlist_file = open(resource_filename(
    'kalite',
    'playlist/data/playlists.json'
))
UNITS = sorted(set([p["unit"] for p in json.load(playlist_file)]))