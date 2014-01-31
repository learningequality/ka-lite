import glob
import json
import os

def get_language_alist(localepaths):
    for localepath in localepaths:
        for langdir in os.listdir(localepath):
            mdfile = glob.glob(os.path.join(localepath, langdir, '*_metadata.json'))[0]
            with open(mdfile) as f:
                metadata = json.load(f)
            lc = metadata['code'].lower() # django reads language codes in lowercase
            yield (lc, metadata['name'])
