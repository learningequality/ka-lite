import glob
import json
import os

def get_language_alist(localepaths):
    for localepath in localepaths:
        for langdir in os.listdir(localepath):
            try:
                mdfiles = glob.glob(os.path.join(localepath, langdir, '*_metadata.json'))
                for mdfile in mdfiles:
                    with open(mdfile) as f:
                        metadata = json.load(f)
                    lc = metadata['code'].lower() # django reads language codes in lowercase
                    yield (lc, metadata['name'])
                    break
            except Exception as e:
                logging.error("Error loading metadata: %s" % e)

