import logging
import json
import re 
import requests
import os

from kalite import settings

def make_request(headers, url, max_retries=5):
    """Return response from url; retry up to 5 times for server errors.
    When returning an error, return human-readable status code.

    codes: server-error, client-error
    """
    for retries in range(1, 1 + max_retries):
        try:
            r = requests.get(url, headers=headers)
            if r.status_code > 499:
                if retries == max_retries:
                    logging.warn(
                        "Error downloading %s: server-side error (%d)" % (url, r.status_code))
                    r = "server-error"
                    break;
            elif r.status_code > 399:
                logging.warn(
                    "Error downloading %s: client-side error (%d)" % (url, r.status_code))
                r = "client-error"
                break
            # TODO(dylan): if internet connection goes down, we aren't catching
            # that, and things just break
            else:
                break
        except Exception as e:
            logging.warn("Error downloading %s: %s" % (url, e))
    return r


def get_language_name(lang_code, native=False):
    """Return full English or native language name from ISO 639-1 language code; raise exception if it isn't hardcoded yet"""
    # Open lookup dictionary 
    lang_lookup_filename = "languagelookup.json"
    lang_lookup_path = os.path.join(settings.DATA_PATH, lang_lookup_filename)
    LANGUAGE_LOOKUP = json.loads(open(lang_lookup_path).read())

    # Convert code if neccessary 
    lang_code = convert_language_code(lang_code)

    language_entry = LANGUAGE_LOOKUP.get(lang_code)    
    if not language_entry:
       raise Exception("We don't have language code '%s' saved in our lookup dictionary (location: %s). Please manually add it before re-running this command." % (lang_code, lang_lookup_path))

    if not native:
        language_name = language_entry["name"]
    else:
        language_name = language_entry["native_name"]

    return language_name


def convert_language_code(lang_code, for_crowdin=False):
    """
    Return language code for lookup in local dictionary. 

    Note: For language codes with localizations, Django requires the format xx_XX (e.g. Spanish from Spain = es_ES)  
    not: xx-xx, xx-XX, xx_xx.
    """
    lang_code = lang_code.lower()
    code_parts = re.split('-|_', lang_code)    
    if len(code_parts) >  1:
        assert len(code_parts) == 2
        code_parts[1] = code_parts[1].upper()
        if not for_crowdin:
            lang_code = "_".join(code_parts)
        else:
            lang_code = "-".join(code_parts)

    return lang_code
