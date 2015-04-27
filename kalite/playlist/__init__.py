import json, os
UNITS = sorted(set([p["unit"] for p in json.load(open(os.path.join(os.path.dirname(__file__), 'playlists.json')))]))