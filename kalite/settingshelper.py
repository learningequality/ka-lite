import glob
import json
import os

def allow_all_languages_alist(langlookupfile):
    with open(langlookupfile) as f:
        langlookup = json.load(f)
    for lc, metadata in langlookup.iteritems():
        lc = (lc.
              lower().          # django only accepts lowercase languages
              replace('-', '_') # django needs the underscore
        )
        yield (lc, metadata['name'])

def allow_languages_in_locale_path_alist(localepaths):
    for localepath in localepaths:
        langdirs = os.listdir(localepath) if os.path.exists(localepath) else []
        for langdir in langdirs:
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
